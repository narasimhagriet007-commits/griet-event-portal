"""
GRIET Event Registration Platform - FastAPI backend.

Run:  uvicorn main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
import logging
import os
import re
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator
from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

try:  # optional .env support
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("griet")

# In-memory duplicate UTR tracking for quick client-side validation and audit checks.
existing_utrs: set[str] = set()

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./griet_events.db")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if o.strip()]
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

UPI_VPA = os.getenv("UPI_VPA", "griet@upi")  # payee address that receives fees
UPI_PAYEE_NAME = os.getenv("UPI_PAYEE_NAME", "GRIET Events")
AUTO_VERIFY_UPI = os.getenv("AUTO_VERIFY_UPI", "true").lower() == "true"

# Google Sheets sync: "webhook" (Apps Script URL), "api" (service account), or "off"
SHEETS_MODE = os.getenv("SHEETS_MODE", "off").lower()
SHEETS_WEBHOOK_URL = os.getenv("SHEETS_WEBHOOK_URL", "")
GOOGLE_CREDS_FILE = os.getenv("GOOGLE_CREDS_FILE", "service_account.json")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_SHEET_TAB = os.getenv("GOOGLE_SHEET_TAB", "Registrations")

# --------------------------------------------------------------------------- #
# Events catalogue (dynamic pricing: early-bird until a deadline, then regular)
# --------------------------------------------------------------------------- #
EVENTS: dict[str, dict] = {
    "hackathon": {
        "name": "GRIET Hackathon",
        "description": "24-hour team hackathon.",
        "date": date(2026, 11, 21),
        "venue": "Main Auditorium, GRIET",
        "regular_price": 300,
        "early_bird_price": 200,
        "early_bird_until": date(2026, 11, 5),
    },
    "meetup": {
        "name": "Tech Meetup",
        "description": "Student and industry developer meetup.",
        "date": date(2026, 11, 14),
        "venue": "Seminar Hall 2, GRIET",
        "regular_price": 100,
        "early_bird_price": 50,
        "early_bird_until": date(2026, 11, 7),
    },
    "tech-talk": {
        "name": "Tech Talk",
        "description": "Guest lecture series by industry speakers.",
        "date": date(2026, 11, 18),
        "venue": "Conference Hall, GRIET",
        "regular_price": 50,
        "early_bird_price": 0,
        "early_bird_until": date(2026, 11, 10),
    },
    "fest": {
        "name": "GRIET Fest",
        "description": "Annual campus cultural and tech fest.",
        "date": date(2026, 12, 5),
        "venue": "GRIET Campus",
        "regular_price": 500,
        "early_bird_price": 350,
        "early_bird_until": date(2026, 11, 25),
    },
}


def current_price(event: dict, today: Optional[date] = None) -> int:
    today = today or date.today()
    return event["early_bird_price"] if today <= event["early_bird_until"] else event["regular_price"]


def build_upi_payload(event_id: str, event: dict, amount: int) -> dict:
    ref = f"GRIET-{event_id.upper()}"
    params = {"pa": UPI_VPA, "pn": UPI_PAYEE_NAME, "am": f"{amount:.2f}", "cu": "INR", "tn": f"{event['name']} registration", "tr": ref}
    return {"params": params, "uri": "upi://pay?" + urlencode(params)}


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (UniqueConstraint("roll_number", "event_id", name="uq_roll_event"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(10))
    year: Mapped[int] = mapped_column(Integer)
    branch: Mapped[str] = mapped_column(String(40))
    roll_number: Mapped[str] = mapped_column(String(12), index=True)
    event_id: Mapped[str] = mapped_column(String(30), index=True)
    payment_method: Mapped[str] = mapped_column(String(10))
    transaction_utr: Mapped[Optional[str]] = mapped_column(String(12), unique=True, nullable=True)
    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(25), default="pending_verification")
    sheet_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    sheet_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #
class PaymentMethod(str, Enum):
    UPI = "UPI"
    CASH = "CASH"


class RegistrationIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str
    year: int = Field(ge=1, le=4, description="Year of study (1-4)")
    branch: str = Field(min_length=2, max_length=40)
    roll_number: str
    event_id: str
    payment_method: PaymentMethod
    txnId: Optional[str] = None
    transaction_utr: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _coalesce_utr_alias(cls, data):
        if isinstance(data, dict):
            txn_id = data.get("txnId")
            utr = data.get("transaction_utr")
            if utr is None and txn_id not in (None, ""):
                data["transaction_utr"] = txn_id
        return data

    @field_validator("name", "branch", mode="before")
    @classmethod
    def _strip(cls, v):
        return " ".join(v.split()) if isinstance(v, str) else v

    @field_validator("branch")
    @classmethod
    def _branch(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9 &()\-.]{2,40}", v):
            raise ValueError("Branch contains invalid characters")
        return v.upper()

    @field_validator("phone", mode="before")
    @classmethod
    def _phone(cls, v):
        if not isinstance(v, str):
            v = str(v)
        digits = re.sub(r"[\s\-]", "", v)
        digits = re.sub(r"^(\+91|91|0)(?=\d{10}$)", "", digits)
        if not re.fullmatch(r"[6-9]\d{9}", digits):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return digits

    @field_validator("roll_number", mode="before")
    @classmethod
    def _roll(cls, v):
        v = str(v).strip().upper()
        if not re.fullmatch(r"[A-Z0-9]{8,12}", v):
            raise ValueError("Roll number must be 8-12 letters/digits")
        return v

    @field_validator("event_id", mode="before")
    @classmethod
    def _event(cls, v):
        return str(v).strip().lower()

    @field_validator("payment_method", mode="before")
    @classmethod
    def _method(cls, v):
        return v.strip().upper() if isinstance(v, str) else v

    @field_validator("transaction_utr", mode="before")
    @classmethod
    def _utr(cls, v, info: ValidationInfo):
        method = info.data.get("payment_method")
        source = v if isinstance(v, str) and v.strip() else info.data.get("txnId")
        v = source.strip() if isinstance(source, str) and source.strip() else None
        if method == PaymentMethod.UPI:
            if v is None:
                raise ValueError("transaction_utr is required for UPI payments")
            if not re.fullmatch(r"\d{12}", v):
                raise ValueError("UTR must be exactly 12 digits")
        elif method == PaymentMethod.CASH and v is not None:
            raise ValueError("transaction_utr must be empty for cash payments")
        return v


class RegistrationOut(BaseModel):
    id: int
    name: str
    roll_number: str
    event_id: str
    event_name: str
    payment_method: str
    transaction_utr: Optional[str]
    amount: int
    status: str
    created_at: datetime


# --------------------------------------------------------------------------- #
# Error helpers
# --------------------------------------------------------------------------- #
class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details=None):
        self.status_code, self.code, self.message, self.details = status_code, code, message, details


def error_response(status: int, code: str, message: str, details=None) -> JSONResponse:
    body = {"success": False, "error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status, content=body)


# --------------------------------------------------------------------------- #
# Google Sheets sync
# --------------------------------------------------------------------------- #
SHEET_HEADERS = ["Registration ID", "Timestamp (UTC)", "Name", "Phone", "Year", "Branch", "Roll Number",
                 "Event", "Payment Method", "UTR", "Amount (INR)", "Status"]
_gspread_ws = None


def _row_for(reg: Registration) -> list:
    return [reg.id, reg.created_at.strftime("%Y-%m-%d %H:%M:%S"), reg.name, reg.phone, reg.year, reg.branch,
            reg.roll_number, EVENTS[reg.event_id]["name"], reg.payment_method, reg.transaction_utr or "",
            reg.amount, reg.status]


def _append_via_api(row: list) -> None:
    global _gspread_ws
    import gspread

    if _gspread_ws is None:
        ws = gspread.service_account(filename=GOOGLE_CREDS_FILE).open_by_key(GOOGLE_SHEET_ID).worksheet(GOOGLE_SHEET_TAB)
        if not ws.row_values(1):
            ws.append_row(SHEET_HEADERS)
        _gspread_ws = ws
    _gspread_ws.append_row(row, value_input_option="USER_ENTERED")


def _append_via_webhook(row: list) -> None:
    payload = {"headers": SHEET_HEADERS, "row": row, "record": dict(zip(SHEET_HEADERS, row))}
    with httpx.Client(timeout=15, follow_redirects=True) as client:
        client.post(SHEETS_WEBHOOK_URL, json=payload).raise_for_status()


def sync_registration_to_sheet(reg_id: int) -> None:
    """Background job: append a verified registration to the sheet exactly once."""
    if SHEETS_MODE == "off":
        return
    with SessionLocal() as db:
        reg = db.get(Registration, reg_id)
        if reg is None or reg.status != "verified" or reg.sheet_synced:
            return
        try:
            row = _row_for(reg)
            if SHEETS_MODE == "api":
                _append_via_api(row)
            elif SHEETS_MODE == "webhook":
                _append_via_webhook(row)
            else:
                raise RuntimeError(f"Unknown SHEETS_MODE '{SHEETS_MODE}'")
            reg.sheet_synced, reg.sheet_error = True, None
        except Exception as exc:  # never fail the registration because of Sheets
            log.exception("Sheet sync failed for registration %s", reg_id)
            global _gspread_ws
            _gspread_ws = None
            reg.sheet_error = str(exc)[:500]
        db.commit()


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for utr in db.scalars(select(Registration.transaction_utr).where(Registration.transaction_utr.is_not(None))):
            if utr:
                existing_utrs.add(utr.strip())
    yield


app = FastAPI(title="GRIET Event Registration API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve files from the backend folder (e.g. myqr.jpeg for UPI QR or pass assets)
app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")


@app.exception_handler(AppError)
async def _app_error(_: Request, exc: AppError):
    return error_response(exc.status_code, exc.code, exc.message, exc.details)


@app.exception_handler(RequestValidationError)
async def _validation_error(_: Request, exc: RequestValidationError):
    details = [
        {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"].removeprefix("Value error, ")}
        for e in exc.errors()
    ]
    return error_response(422, "validation_error", "One or more fields are invalid", details)


@app.exception_handler(StarletteHTTPException)
async def _http_error(_: Request, exc: StarletteHTTPException):
    return error_response(exc.status_code, "http_error", str(exc.detail))


@app.exception_handler(Exception)
async def _unhandled(_: Request, exc: Exception):
    log.exception("Unhandled error")
    return error_response(500, "internal_error", "Something went wrong. Please try again.")


def require_admin(x_admin_key: str = Header(default="")):
    if not ADMIN_API_KEY:
        raise AppError(503, "admin_disabled", "ADMIN_API_KEY is not configured")
    if x_admin_key != ADMIN_API_KEY:
        raise AppError(401, "unauthorized", "Invalid admin key")


@app.get("/health")
def health():
    return {"success": True, "status": "ok"}


@app.get("/code.html", include_in_schema=False)
def serve_frontend():
    return FileResponse(BASE_DIR.parent / "frontend" / "code.html")


@app.get("/api/events")
def list_events():
    today = date.today()
    out = []
    for event_id, ev in EVENTS.items():
        price = current_price(ev, today)
        early = today <= ev["early_bird_until"]
        out.append({
            "id": event_id,
            "name": ev["name"],
            "description": ev["description"],
            "date": ev["date"].isoformat(),
            "venue": ev["venue"],
            "pricing": {
                "currency": "INR",
                "current_price": price,
                "regular_price": ev["regular_price"],
                "early_bird_price": ev["early_bird_price"],
                "early_bird_active": early,
                "early_bird_until": ev["early_bird_until"].isoformat(),
            },
            "upi": build_upi_payload(event_id, ev, price) if price > 0 else None,
        })
    return {"success": True, "data": out}


@app.post("/api/register", status_code=201)
def register(payload: RegistrationIn, background: BackgroundTasks, db: Session = Depends(get_db)):
    event = EVENTS.get(payload.event_id)
    if event is None:
        raise AppError(404, "event_not_found", f"Unknown event '{payload.event_id}'",
                       {"valid_event_ids": list(EVENTS)})
    if event["date"] < date.today():
        raise AppError(400, "registration_closed", "Registration for this event has closed")

    if db.scalar(select(Registration.id).where(Registration.roll_number == payload.roll_number,
                                               Registration.event_id == payload.event_id)):
        raise AppError(409, "already_registered", "This roll number is already registered for this event")
    if payload.transaction_utr and db.scalar(select(Registration.id).where(Registration.transaction_utr == payload.transaction_utr)):
        raise AppError(409, "duplicate_utr", "This transaction UTR has already been used")

    # Duplicate UTR guard for faster validation and audit tracking in-memory.
    if payload.transaction_utr:
        utr = payload.transaction_utr.strip()
        if not (utr.isdigit() and len(utr) == 12):
            raise AppError(400, "invalid_utr", "Invalid UTR! Must be a 12-digit transaction ID.")
        if utr in existing_utrs:
            raise AppError(409, "duplicate_utr", "This UTR has already been submitted!")

    amount = current_price(event)  # always computed server-side, never trusted from client
    if payload.payment_method == PaymentMethod.UPI and amount == 0:
        raise AppError(400, "payment_not_required", "This event is free right now; use CASH/no payment flow")

    status = "verified" if (payload.payment_method == PaymentMethod.UPI and AUTO_VERIFY_UPI) or amount == 0 else "pending_verification"
    reg = Registration(
        name=payload.name, phone=payload.phone, year=payload.year, branch=payload.branch,
        roll_number=payload.roll_number, event_id=payload.event_id,
        payment_method=payload.payment_method.value, transaction_utr=payload.transaction_utr,
        amount=amount, status=status,
    )
    db.add(reg)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "duplicate_registration", "Duplicate registration or UTR detected")

    if payload.transaction_utr:
        existing_utrs.add(payload.transaction_utr.strip())

    if reg.status == "verified":
        background.add_task(sync_registration_to_sheet, reg.id)

    return {"success": True, "message": "Registration received", "data": _out(reg)}


def _out(reg: Registration) -> dict:
    return RegistrationOut(
        id=reg.id, name=reg.name, roll_number=reg.roll_number, event_id=reg.event_id,
        event_name=EVENTS[reg.event_id]["name"], payment_method=reg.payment_method,
        transaction_utr=reg.transaction_utr, amount=reg.amount, status=reg.status, created_at=reg.created_at,
    ).model_dump(mode="json")


# ----------------------------- Admin endpoints ----------------------------- #
@app.post("/api/admin/registrations/{reg_id}/verify", dependencies=[Depends(require_admin)])
def verify_registration(reg_id: int, background: BackgroundTasks, db: Session = Depends(get_db)):
    reg = db.get(Registration, reg_id)
    if reg is None:
        raise AppError(404, "not_found", "Registration not found")
    reg.status = "verified"
    db.commit()
    background.add_task(sync_registration_to_sheet, reg.id)
    return {"success": True, "data": _out(reg)}


@app.post("/api/admin/sync-pending", dependencies=[Depends(require_admin)])
def sync_pending(db: Session = Depends(get_db)):
    """Retry sheet sync for verified registrations that failed earlier."""
    ids = db.scalars(select(Registration.id).where(Registration.status == "verified", Registration.sheet_synced.is_(False))).all()
    for rid in ids:
        sync_registration_to_sheet(rid)
    return {"success": True, "attempted": len(ids)}


@app.get("/api/admin/registrations", dependencies=[Depends(require_admin)])
def list_registrations(event_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = select(Registration).order_by(Registration.id.desc())
    if event_id:
        q = q.where(Registration.event_id == event_id)
    return {"success": True, "data": [_out(r) | {"sheet_synced": r.sheet_synced, "sheet_error": r.sheet_error} for r in db.scalars(q)]}

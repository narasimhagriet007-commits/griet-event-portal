# GRIET payment reconciliation (webhook adapter)

Python 3.9+, standard library only. No pip dependencies.

## Run

Set GRIET_WEBHOOK_URL to your HTTPS endpoint and GRIET_WEBHOOK_TOKEN to a secret.

```bash
export GRIET_WEBHOOK_URL="https://your-webhook.example/reconcile"
export GRIET_WEBHOOK_TOKEN="your-secret"
python reconcile_griet.py --payments payments_example.json --dry-run
python reconcile_griet.py --payments payments_example.json --trusted-source
```

Without --trusted-source no new payment is marked verified. Use that option only
for independently bank/provider-confirmed payments authenticated upstream. A
12-digit UTR is a formatting check, NOT proof of payment. Do not trust a student's
self-reported success status, screenshot, or UTR alone. The script does not implement
provider-specific signature verification. Adapt/verify upstream before enabling it.
Amounts are INR rupees (not paise); normalize provider payloads first. Registration
ID is the matching key, not student name. Keep UTRs as text in Sheets and JSON,
including leading zeros. The 12-digit rule is the requested business rule and is
not asserted to cover every payment provider's identifier format.

## Required existing webhook contract

The script is the CLIENT, not a webhook server. Implement these actions in your
existing endpoint, or an Apps Script connected to your Google Sheet. Every request
is HTTPS POST JSON with action and token. Validate the secret on the server and
restrict sheet access. Do not expose unauthenticated writes or log tokens.

### list_registrations
Request: {"action":"list_registrations", "token":"..."}
Response:
```json
{"ok":true,"registrations":[{"registration_id":"REG001","event":"Tech Fest",
 "branch":"CSE","expected_amount":"500.00","payment_status":"pending",
 "utr":"","paid_amount":""}]}
```

These exact field names are required; map your sheet headers in the endpoint.
Each row represents one unique event registration. Allowed sheet status examples:
pending, failed, needs_review, verified. Only verified counts as collected revenue.
Expected amounts must be positive and have at most two decimal places.

### verify_payment
Request:
```json
{"action":"verify_payment","token":"...","registration_id":"REG001",
 "utr":"012345678901","paid_amount":"500.00","currency":"INR",
 "expected_amount":"500.00"}
```
Response: {"ok":true,"status":"verified"} or
{"ok":true,"status":"already_verified"}.
Failure: {"ok":false,"error":"reason"}, optionally an appropriate HTTP error.

CRITICAL server guarantees: validate fields again; authenticate the caller;
atomically lock/check/update the sheet (e.g. Apps Script LockService); require an
existing unique registration ID; check its current expected amount; reject a UTR
already assigned to a different registration; reject replacement of a verified
payment; make identical repeated writes idempotent. Never blindly overwrite cells.
These checks are required to prevent races across multiple clients. Match existing
verified payments on registration ID, UTR, amount, and currency.

## Inputs and reports

Accepts a single JSON object, JSON array, {"payments":[...]}, or .jsonl file.
Fields: registration_id, utr (aliases transaction_id or UTR), amount, status,
currency (defaults INR), event (optional cross-check). Accepted successful statuses:
success, successful, captured, paid. All others remain pending. Matching is exact.
Conflicts/invalid inputs go to the audit report without changing sheet records.
Pending payload outcomes do not overwrite existing sheet statuses or UTRs.

The chosen output directory receives summary.json and payment_audit.csv. Summary:
- Revenue per event and overall from authoritative verified rows only.
- Event/branch registration counts across ALL registration rows, paid or unpaid.
- Pending payment count and registration details (all non-verified rows).
- Counts of payload outcomes, including needs_review and authenticity-pending.

Dry-run reads the webhook but never writes; metrics reflect current sheet revenue,
not hypothetical revenue. Network/API failures stop the run and reports may not be
created; rerun safely once the endpoint is fixed (server idempotency required).
Reports include student registration identifiers: restrict access and retention.
No refunds, partial payments, split payments, fee waivers, or cancellations are
modeled. Revenue means gross verified collections, not net revenue after refunds.
For scheduled execution use cron/Task Scheduler with protected secret environment
variables. This client processes files; a live incoming webhook receiver needs a
separate authenticated service or upstream export job.

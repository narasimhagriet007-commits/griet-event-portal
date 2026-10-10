import streamlit as st
import os

# Page Config
st.set_page_config(
    page_title="GRIET Event Portal",
    page_icon="🎓",
    layout="centered"
)

# Session State Initializations
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'registered_utrs' not in st.session_state:
    st.session_state.registered_utrs = set()

st.title("🎓 GRIET Campus Event Portal")
st.write("Official Autonomous Event Registration & Digital E-Pass System")

# Event Options
EVENTS = {
    "HackGRIET 2026": {"fee": "₹300 / team", "tag": "36-Hour Hackathon"},
    "DevConnect Meetup": {"fee": "₹150", "tag": "Open Source & Cloud"},
    "AI Summit 2026": {"fee": "₹200", "tag": "Research Colloquium"},
    "PULSE 2026": {"fee": "₹250", "tag": "Annual Cultural Fest"}
}

# --- STEP 1: Registration Form ---
if st.session_state.step == 1:
    st.subheader("Step 1: Student Details")
    
    selected_event = st.selectbox("Select Event", list(EVENTS.keys()))
    st.info(f"Fee: **{EVENTS[selected_event]['fee']}** | Tag: *{EVENTS[selected_event]['tag']}*")
    
    with st.form("registration_form"):
        full_name = st.text_input("Full Name", placeholder="e.g. Rahul Varma")
        roll_number = st.text_input("Roll / Hall Ticket No.", placeholder="e.g. 21241A05XX").upper()
        phone = st.text_input("Phone Number (+91)", placeholder="9876543210")
        year = st.selectbox("Year of Study", ["I", "II", "III", "IV"])
        branch = st.selectbox("Branch", ["CSE", "AIML", "DS", "IT", "ECE", "EEE", "MECH", "CIVIL"])
        
        submit_btn = st.form_submit_button("Proceed to UPI Payment")

    if submit_btn:
        if not full_name or not roll_number or not phone:
            st.error("Please fill in all required fields!")
        else:
            st.session_state.user_data = {
                "name": full_name,
                "roll": roll_number,
                "phone": phone,
                "year": year,
                "branch": branch,
                "event": selected_event,
                "fee": EVENTS[selected_event]['fee']
            }
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: UPI Payment & UTR Fraud Verification ---
elif st.session_state.step == 2:
    data = st.session_state.user_data
    st.subheader("Step 2: Scan QR & Confirm Payment")
    
    st.markdown(f"**Student:** {data['name']} ({data['roll']})")
    st.markdown(f"**Event:** {data['event']} — **{data['fee']}**")

    # Display Payment QR
    qr_path = "backend/myqr.jpeg" if os.path.exists("backend/myqr.jpeg") else "myqr.jpeg"
    if os.path.exists(qr_path):
        st.image(qr_path, caption="Scan QR via any UPI App", width=250)
    else:
        st.warning("QR Code image file (`myqr.jpeg`) not found in backend folder.")

    utr_input = st.text_input("Enter 12-Digit UPI / UTR Transaction ID", max_chars=12, placeholder="123456789012")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.step = 1
            st.rerun()
            
    with col2:
        if st.button("Verify & Generate Pass"):
            utr_clean = utr_input.strip()
            if not (utr_clean.isdigit() and len(utr_clean) == 12):
                st.error("❌ Invalid UTR! Must be exactly 12 numeric digits.")
            elif utr_clean in st.session_state.registered_utrs:
                st.error("🚨 Anti-Fraud Alert: This UTR has already been used!")
            else:
                st.session_state.registered_utrs.add(utr_clean)
                st.session_state.user_data["utr"] = utr_clean
                st.session_state.user_data["pass_id"] = f"GRIET-2026-{utr_clean[-4:]}"
                st.session_state.step = 3
                st.rerun()

# --- STEP 3: E-Pass Confirmation & Download ---
elif st.session_state.step == 3:
    data = st.session_state.user_data
    st.balloons()
    st.success("🎉 Registration Confirmed!")

    st.markdown("---")
    st.markdown(f"""
    ### 🎟️ OFFICIAL GRIET DIGITAL E-PASS
    * **Pass ID:** `{data['pass_id']}`
    * **Student Name:** {data['name']}
    * **Roll No:** {data['roll']}
    * **Department:** {data['branch']} (Year {data['year']})
    * **Event Registered:** {data['event']}
    * **UTR Reference:** `{data['utr']}`
    * **Status:** Verified ✅
    ---
    """)

    pass_text = f"""
========================================
   GOKARAJU RANGARAJU INSTITUTE OF 
      ENGINEERING & TECHNOLOGY
        OFFICIAL E-PASS 2026
========================================
PASS ID   : {data['pass_id']}
NAME      : {data['name']}
ROLL NO   : {data['roll']}
DEPT      : {data['branch']} (Year {data['year']})
EVENT     : {data['event']}
UTR REF   : {data['utr']}
STATUS    : VERIFIED ✅
========================================
    """
    
    st.download_button(
        label="📥 Download Digital Pass Ticket",
        data=pass_text,
        file_name=f"GRIET_EPass_{data['roll']}.txt",
        mime="text/plain"
    )

    if st.button("Register Another Student"):
        st.session_state.step = 1
        st.rerun()
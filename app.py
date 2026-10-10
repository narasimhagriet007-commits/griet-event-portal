import streamlit as st
import requests

st.set_page_config(page_title="GRIET Event Portal", page_icon="🎓")

st.title("GRIET Campus Event Portal")
st.write("Welcome to the official GRIET event registration system.")

# Form
with st.form("registration_form"):
    full_name = st.text_input("Full Name")
    roll_number = st.text_input("Roll Number")
    phone = st.text_input("Phone Number")
    submitted = st.form_submit_button("Proceed to Pay")

if submitted:
    st.success(f"Details saved for {full_name} ({roll_number})!")
    st.image("backend/myqr.jpeg", caption="Scan QR code to pay via UPI", width=250)
    
    utr = st.text_input("Enter 12-digit UTR/Txn ID")
    if st.button("Confirm Payment"):
        if len(utr) == 12:
            st.balloons()
            st.success("E-Pass Generated Successfully!")
        else:
            st.error("Please enter a valid 12-digit UTR ID.")

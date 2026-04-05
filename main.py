import streamlit as st
from app.login import login
from dashboard.dashboard import run_dashboard

# ---------------- SESSION INIT ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------------- LOGIN FLOW ----------------
if not st.session_state.logged_in:
    login()
    st.stop()

# ---------------- DASHBOARD ----------------
run_dashboard()
import streamlit as st
from app.login import login
from dashboard.dashboard import run_dashboard

# LOGIN
if not login():
    st.stop()

# DASHBOARD
run_dashboard()
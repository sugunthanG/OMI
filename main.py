import streamlit as st
from dashboard.dashboard import run_dashboard

st.session_state.logged_in = True

if __name__ == "__main__":
    run_dashboard()
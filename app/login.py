import streamlit as st
import hashlib

# =========================
# 👑 SUPERADMIN
# =========================
SUPERADMIN_ID = "Superadmin"
SUPERADMIN_PASSWORD = hashlib.sha256("Super@8520".encode()).hexdigest()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =========================
# 🚪 LOGIN
# =========================
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    # ================= CSS =================
    st.markdown("""
    <style>

    * {
        box-sizing: border-box;
    }

    html, body, [data-testid="stAppViewContainer"] {
        margin: 0;
        padding: 0;
        height: 100%;
        overflow: hidden;
        background: radial-gradient(circle at top, #0f172a, #020617);
        color: white;
    }

    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }

    header, footer {
        visibility: hidden;
    }

    /* MAIN */
    .main-box {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;

        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    /* TOP */
    .top {
        text-align: center;
        margin-top: 50px;
    }

    .top h1 {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(90deg, #38bdf8, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .top p {
        color: #94a3b8;
        font-size: 14px;
    }

    /* CENTER */
    .center {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* CARD */
    .card {
        width: 380px;
        padding: 35px;
        border-radius: 18px;

        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(25px);

        border: 1px solid rgba(255,255,255,0.08);

        box-shadow: 0 10px 40px rgba(0,0,0,0.7);

        text-align: center;
    }

    /* INPUT */
    input {
        background-color: #020617 !important;
        border: 1px solid #1e293b !important;
        color: white !important;
        border-radius: 10px !important;
        height: 42px !important;
    }

    /* BUTTON */
    .stButton>button {
        width: 100%;
        margin-top: 12px;
        height: 45px;
        border-radius: 10px;
        background: linear-gradient(90deg, #2563eb, #4f46e5);
        color: white;
        font-weight: 600;
        border: none;
    }

    .stButton>button:hover {
        background: linear-gradient(90deg, #1d4ed8, #4338ca);
    }

    /* FOOTER */
    .bottom {
        text-align: center;
        margin-bottom: 20px;
        color: #64748b;
        font-size: 13px;
    }

    </style>
    """, unsafe_allow_html=True)

    # ================= UI =================

    st.markdown('<div class="main-box">', unsafe_allow_html=True)

    # 🔝 TOP
    st.markdown("""
    <div class="top">
        <h1>🚀 Welcome to OMI</h1>
        <p>Orion Market Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    # 🎯 CENTER
    st.markdown('<div class="center">', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    user = st.text_input("User ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == SUPERADMIN_ID and hash_password(password) == SUPERADMIN_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.user = {
                "username": user,
                "role": "superadmin"
            }
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.markdown('</div>', unsafe_allow_html=True)  # card
    st.markdown('</div>', unsafe_allow_html=True)  # center

    # 🔻 FOOTER
    st.markdown("""
    <div class="bottom">
        ⚡ Powered by AEGIS
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # main-box

    return st.session_state.logged_in


# =========================
# 🚪 LOGOUT
# =========================
def logout():
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()
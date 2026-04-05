# =========================================
# OMI DASHBOARD (FINAL PRO FIXED)
# =========================================

import sys, os
from datetime import datetime, UTC

import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ---------------- PATH SETUP ----------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ---------------- IMPORTS ----------------
from app.login import logout
from app.data import fetch_data
from app.features import create_features
from app.signals import generate_signal, FEATURES
from app.model import load_model
from app.whatsapp_api import send_whatsapp
from app.backtester import run_backtest
from app.trade_tracker import update_trades

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

MODEL_PATH = "models/gold_model_v2.pkl"

# =========================
# MODEL
# =========================
@st.cache_resource
def get_model(path):
    return load_model(path)


def run_dashboard():

    # =========================
    # SIDEBAR
    # =========================
    def sidebar_controls():
        with st.sidebar:
            st.markdown("## ⚙️ CONTROL PANEL")
            logout()

            st.caption(f"Using: {MODEL_PATH}")
            st.markdown("---")

            auto_refresh = st.toggle("🔄 Auto Refresh", True)
            refresh_interval = st.slider("Refresh (sec)", 10, 120, 30)

            if st.button("🔁 Refresh Now"):
                st.rerun()

            st.markdown("---")

            timeframe = st.selectbox("🧠 Timeframe", ["5m", "15m", "1h"])

            st.markdown("---")

            risk_mode = st.radio("⚡ Risk Mode", ["Conservative", "Balanced", "Aggressive"])
            sound_alert = st.toggle("🔊 Sound Alert", False)

            st.markdown("---")

            whatsapp_alert = st.toggle("📲 WhatsApp Alert", False)
            phone = st.text_input("WhatsApp Number", "+91XXXXXXXXXX") if whatsapp_alert else None

        return timeframe, risk_mode, sound_alert, whatsapp_alert, phone, auto_refresh, refresh_interval

    timeframe, risk_mode, sound_alert, whatsapp_alert, phone, auto_refresh, refresh_interval = sidebar_controls()

    # =========================
    # LOAD MODEL
    # =========================
    if not os.path.exists(MODEL_PATH):
        st.error("Model not found")
        st.stop()

    model = get_model(MODEL_PATH)

    # =========================
    # SESSION INIT
    # =========================
    if "active_trades" not in st.session_state:
        st.session_state.active_trades = []

    if "signal_history" not in st.session_state:
        st.session_state.signal_history = []

    if "capital" not in st.session_state:
        st.session_state.capital = 10000

    if "equity_curve" not in st.session_state:
        st.session_state.equity_curve = []

    if "last_signal" not in st.session_state:
        st.session_state.last_signal = None

    # =========================
    # DATA
    # =========================
    df = fetch_data()
    df = create_features(df)

    for f in FEATURES:
        if f not in df.columns:
            df[f] = 0

    df = df.dropna()

    # =========================
    # SIGNAL
    # =========================
    signal, prob, entry, atr = generate_signal(model, df)

    if prob < 0.65:
        signal = "NO TRADE"

    price = float(df["Close"].iloc[-1])

    # =========================
    # RISK
    # =========================
    if signal == "BUY":
        sl = entry - atr * 1.5
        tp = entry + atr * 3
    elif signal == "SELL":
        sl = entry + atr * 1.5
        tp = entry - atr * 3
    else:
        sl, tp = None, None

    # =========================
    # HEADER
    # =========================
    st.title("🟡 OMI TERMINAL")

    col1, col2, col3 = st.columns(3)

    col1.metric("Price", round(price, 2))
    col2.metric("Signal", signal)
    col3.metric("Confidence", round(prob, 2))

    # =========================
    # TRADINGVIEW
    # =========================
    st.components.v1.html("""
    <script src="https://s3.tradingview.com/tv.js"></script>
    <div id="tv_chart"></div>
    <script>
    new TradingView.widget({
        width: "100%",
        height: 500,
        symbol: "OANDA:XAUUSD",
        interval: "5",
        theme: "light",
        container_id: "tv_chart"
    });
    </script>
    """, height=520)

    # =========================
    # METRICS
    # =========================
    st.subheader("📊 Trade Metrics")
    st.write({
        "Entry": entry,
        "SL": sl,
        "TP": tp
    })

    # =========================
    # AI REASON
    # =========================
    st.subheader("🧠 AI Reason")

    ema9 = df["ema9"].iloc[-1] if "ema9" in df else None
    ema21 = df["ema21"].iloc[-1] if "ema21" in df else None
    rsi = df["rsi"].iloc[-1] if "rsi" in df else None

    st.write("Trend:", "Bullish" if ema9 and ema21 and ema9 > ema21 else "Bearish")
    st.write("RSI:", rsi)

    # =========================
    # DEBUG
    # =========================
    st.subheader("🧪 Debug")
    st.write({"EMA9": ema9, "EMA21": ema21, "RSI": rsi, "Confidence": prob})

    # =========================
    # WHATSAPP
    # =========================
    if whatsapp_alert and signal in ["BUY", "SELL"] and phone:
        msg = f"{signal} | Entry:{entry} | SL:{sl} | TP:{tp}"
        send_whatsapp(msg, phone)

    # =========================
    # TRADES
    # =========================
    st.session_state.active_trades = update_trades(st.session_state.active_trades, df)

    st.subheader("📊 Trades")
    st.dataframe(pd.DataFrame(st.session_state.active_trades))

    # =========================
    # EQUITY
    # =========================
    st.session_state.equity_curve.append(st.session_state.capital)
    st.line_chart(st.session_state.equity_curve)

    # =========================
    # BACKTEST
    # =========================
    if st.button("Run Backtest"):
        trades_df, stats = run_backtest(df, model, generate_signal)
        st.write(stats)
        st.dataframe(trades_df)

    # =========================
    # SIGNAL HISTORY
    # =========================
    st.session_state.signal_history.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "signal": signal,
        "price": price
    })

    st.subheader("📜 Signal History")
    st.dataframe(pd.DataFrame(st.session_state.signal_history).tail(20))

    # =========================
    # AUTO REFRESH
    # =========================
    if auto_refresh:
        st_autorefresh(interval=refresh_interval * 1000, key="refresh")
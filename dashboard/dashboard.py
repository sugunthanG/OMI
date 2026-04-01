# =========================================
# OMI DASHBOARD (CLEAN & STRUCTURED VERSION)
# =========================================

import sys, os, glob, time
from datetime import datetime, UTC

import streamlit as st
import pandas as pd

# ---------------- PATH SETUP ----------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ---------------- IMPORTS ----------------
from app.data import fetch_data
from app.features import create_features
from app.signals import generate_signal, FEATURES
from app.model import load_model
from app.whatsapp_api import send_whatsapp
from app.backtester import run_backtest
from app.trade_tracker import update_trades

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

# =========================
# 🔐 AGREEMENT LOCK
# =========================
def agreement_gate():
    if "agreed" not in st.session_state:
        st.session_state.agreed = False

    if not st.session_state.agreed:
        st.markdown("## 🚨 OMI TRADING AGREEMENT REQUIRED")
        st.warning("You must accept rules before using OMI.")

        agree = st.checkbox("✅ I agree to trading rules")

        if st.button("ENTER OMI TERMINAL"):
            if agree:
                st.session_state.agreed = True
                st.rerun()
            else:
                st.error("Please accept rules")
        st.stop()

agreement_gate()

# =========================
# 🧠 SESSION INIT
# =========================
def init_session():
    defaults = {
        "last_signal": None,
        "signal_history": [],
        "trade_log": [],
        "active_trades": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# =========================
# 🌍 SESSION TYPE
# =========================
def get_session():
    hour = datetime.now(UTC).hour
    if hour < 8:
        return "🌏 ASIAN"
    elif hour < 16:
        return "🇬🇧 LONDON"
    return "🇺🇸 NEW YORK"

session = get_session()

# =========================
# 🧠 MODEL HANDLING
# =========================
def get_available_models():
    files = sorted(glob.glob("models/gold_model_v*.pkl"), reverse=True)
    return {
        os.path.basename(f).replace(".pkl", "").replace("gold_model_", ""): f
        for f in files
    }

MODEL_MAP = get_available_models()

@st.cache_resource
def get_model(path):
    return load_model(path)

# =========================
# ⚙️ SIDEBAR
# =========================
def sidebar_controls():
    with st.sidebar:
        st.markdown("## ⚙️ CONTROL PANEL")

        if not MODEL_MAP:
            st.error("No models found")
            st.stop()

        versions = list(MODEL_MAP.keys())
        default_idx = versions.index("v2") if "v2" in versions else 0

        model_version = st.selectbox("🧠 Model Version", versions, index=default_idx)
        model_path = MODEL_MAP[model_version]

        st.caption(f"Using: {model_path}")
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
        phone = st.text_input("Enter WhatsApp Number", "+91XXXXXXXXXX") if whatsapp_alert else None

    return model_path, timeframe, risk_mode, sound_alert, whatsapp_alert, phone, auto_refresh, refresh_interval

model_path, timeframe, risk_mode, sound_alert, whatsapp_alert, phone, auto_refresh, refresh_interval = sidebar_controls()
model = get_model(model_path)

# =========================
# 📊 DATA PIPELINE
# =========================
def get_data(interval):
    df = fetch_data(interval=interval)
    if df is None:
        return None

    df = create_features(df)

    for f in FEATURES:
        if f not in df.columns:
            df[f] = 0

    return df.dropna()


df = get_data(timeframe)

if df is None:
    st.warning("⚠️ Data connection issue... retrying")
    time.sleep(3)
    st.rerun()

# =========================
# 📡 SIGNAL
# =========================
def safe_signal():
    try:
        return generate_signal(model, df)
    except Exception as e:
        st.error(f"Signal Error: {e}")
        return "NO TRADE", 0.0, None, None

signal, prob, entry, atr = safe_signal()
current_price = round(float(df["Close"].iloc[-1]), 2)

# =========================
# 🎯 RISK MANAGEMENT
# =========================
risk_map = {
    "Conservative": (1, 2),
    "Balanced": (1.5, 3),
    "Aggressive": (2, 4)
}

sl_mult, tp_mult = risk_map[risk_mode]

if signal == "BUY" and entry and atr:
    sl, tp = entry - atr * sl_mult, entry + atr * tp_mult
elif signal == "SELL" and entry and atr:
    sl, tp = entry + atr * sl_mult, entry - atr * tp_mult
else:
    sl, tp = None, None

# =========================
# 🖥️ HEADER
# =========================
col1, col2, col3 = st.columns([5, 3, 2])
col1.markdown("### 🟡 OMI TERMINAL")
col2.markdown(f"### {session} SESSION")
col3.metric("📡 PRICE", current_price)

# =========================
# 📊 LAYOUT
# =========================
left, right = st.columns([7, 3])

with left:
    st.components.v1.html("""
    <div id=\"tv_chart\"></div>
    <script src=\"https://s3.tradingview.com/tv.js\"></script>
    <script>
    new TradingView.widget({
        width: "100%",
        height: 600,
        symbol: "OANDA:XAUUSD",
        interval: "5",
        timezone: "Asia/Kolkata",
        theme: "light",
        style: "1",
        container_id: "tv_chart"
    });
    </script>
    """, height=600)

with right:
    st.markdown("### SIGNAL")

    if signal == "BUY": st.success("🟢 BUY")
    elif signal == "SELL": st.error("🔴 SELL")
    else: st.warning("⚪ NO TRADE")

    # 🔊 Sound Alert
    if sound_alert and signal in ["BUY", "SELL"] and st.session_state.last_signal != signal:
        st.components.v1.html("""
        <audio autoplay>
            <source src=\"https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3\">
        </audio>
        """, height=0)

    # 📊 Metrics
    st.markdown("### 📊 Trade Metrics")
    st.metric("📡 Current Price", current_price)
    st.metric("Confidence", round(prob, 2))
    st.metric("Entry", round(entry, 2) if entry else "--")
    st.metric("SL", round(sl, 2) if sl else "--")
    st.metric("TP", round(tp, 2) if tp else "--")

    # 🤖 AI Reason
    ema9, ema21, rsi = df["ema9"].iloc[-1], df["ema21"].iloc[-1], df["rsi"].iloc[-1]

    st.markdown("### 🤖 OMI AI Reason")
    st.write("Trend:", "Bullish" if ema9 > ema21 else "Bearish")
    st.write("RSI:", round(rsi, 2))

    st.markdown("### 🧪 Debug Info")
    st.write({"Confidence": prob, "EMA9": ema9, "EMA21": ema21, "RSI": rsi})

    # 📲 WhatsApp
    if whatsapp_alert and signal in ["BUY", "SELL"] and phone and st.session_state.last_signal != signal:
        msg = f"""Hey User 👋\n\nSignal: {signal}\nEntry: {round(entry,2)}\nSL: {round(sl,2)}\nTP: {round(tp,2)}\nConfidence: {round(prob,2)}\n"""
        send_whatsapp(msg, phone)
        st.session_state.last_signal = signal
        st.success("WhatsApp Sent")

# =========================
# 📊 TRADE TRACKING
# =========================
st.session_state.active_trades = update_trades(st.session_state.active_trades, df)

if signal in ["BUY", "SELL"] and sl and tp:
    last = st.session_state.active_trades[-1] if st.session_state.active_trades else None
    if not last or last["status"] != "OPEN":
        st.session_state.active_trades.append({
            "signal": signal, "entry": entry, "sl": sl, "tp": tp,
            "status": "OPEN", "time": datetime.now().strftime("%H:%M:%S")
        })

# =========================
# 📈 PERFORMANCE
# =========================
st.markdown("### 📊 Live Trade Performance")

trades = pd.DataFrame(st.session_state.active_trades)

if not trades.empty:
    wins = len(trades[trades.status == "WIN"])
    losses = len(trades[trades.status == "LOSS"])
    open_t = len(trades[trades.status == "OPEN"])

    win_rate = (wins / (wins + losses) * 100) if (wins + losses) else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Trades", len(trades))
    c2.metric("Wins", wins)
    c3.metric("Losses", losses)
    c4.metric("Win Rate %", round(win_rate, 2))

    st.write(f"🟡 Open Trades: {open_t}")
    st.dataframe(trades.tail(20), use_container_width=True)
else:
    st.info("No trades yet")

# =========================
# 🔁 BACKTEST
# =========================
st.markdown("---")
st.markdown("### 📊 Strategy Performance")

if st.button("Run Backtest"):
    with st.spinner("Running backtest..."):
        trades_df, stats = run_backtest(df, model, generate_signal)

    if trades_df.empty:
        st.warning("No trades found")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Trades", stats["total_trades"])
        c2.metric("Wins", stats["wins"])
        c3.metric("Losses", stats["losses"])
        c4.metric("Win Rate %", stats["win_rate"])

        st.dataframe(trades_df.tail(20), use_container_width=True)

# =========================
# 📜 SIGNAL HISTORY
# =========================
st.markdown("---")
st.markdown("### 📊 Signal History")

st.session_state.signal_history.append({
    "time": datetime.now().strftime("%H:%M:%S"),
    "signal": signal,
    "price": current_price,
    "confidence": round(prob, 2)
})

st.session_state.signal_history = st.session_state.signal_history[-20:]
st.dataframe(pd.DataFrame(st.session_state.signal_history), use_container_width=True)

# =========================
# 🧾 FOOTER
# =========================
st.markdown("<div style='text-align:right;color:gray;'>Powered by AEGIS</div>", unsafe_allow_html=True)

# =========================
# 🔄 AUTO REFRESH
# =========================
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
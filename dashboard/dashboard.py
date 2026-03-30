import sys
import os
import glob

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import time
from datetime import datetime, UTC

# PIPELINE
from app.data import fetch_data
from app.features import create_features
from app.signals import generate_signal, FEATURES
from app.model import load_model
from app.whatsapp_api import send_whatsapp

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

# ---------------- SESSION STATE ----------------
if "last_signal" not in st.session_state:
    st.session_state.last_signal = None

if "signal_history" not in st.session_state:
    st.session_state.signal_history = []

# ---------------- SESSION ----------------
hour = datetime.now(UTC).hour
session = "🌏 ASIAN" if hour < 8 else "🇬🇧 LONDON" if hour < 16 else "🇺🇸 NEW YORK"

# ---------------- MODEL AUTO DETECT ----------------
def get_available_models():
    files = glob.glob("models/gold_model_v*.pkl")
    files.sort(reverse=True)

    model_map = {}
    for f in files:
        name = os.path.basename(f)
        label = name.replace(".pkl", "").replace("gold_model_", "")
        model_map[label] = f

    return model_map

MODEL_MAP = get_available_models()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## ⚙️ CONTROL PANEL")

    if not MODEL_MAP:
        st.error("No models found")
        st.stop()

    model_versions = list(MODEL_MAP.keys())

    default_index = 0
    for i, v in enumerate(model_versions):
        if v == "v2":
            default_index = i
            break

    model_version = st.selectbox("🧠 Model Version", model_versions, index=default_index)
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
    phone_number = None
    if whatsapp_alert:
        phone_number = st.text_input("Enter WhatsApp Number", "+91XXXXXXXXXX")

# ---------------- MODEL ----------------
@st.cache_resource
def get_model(path):
    return load_model(path)

model = get_model(model_path)

# ---------------- DATA ----------------
@st.cache_data(ttl=10)
def get_data(interval):
    df = fetch_data(interval=interval)
    if df is None:
        return None

    df = create_features(df)
    df.dropna(inplace=True)
    return df

df = get_data(timeframe)

if df is None:
    st.warning("⚠️ Data connection issue... retrying")
    time.sleep(3)
    st.rerun()

# ---------------- FEATURE CHECK (CRITICAL) ----------------
missing = [f for f in FEATURES if f not in df.columns]
if missing:
    st.error(f"❌ Missing features: {missing}")
    st.stop()

# ---------------- SIGNAL ----------------
def safe_signal(df):
    try:
        return generate_signal(model, df)
    except Exception as e:
        st.error(f"Signal Error: {e}")
        return "NO TRADE", 0.0, None, None

signal, prob, entry, atr = safe_signal(df)

# ---------------- CURRENT PRICE ----------------
current_price = round(float(df["Close"].iloc[-1]), 2)

# ---------------- RISK ----------------
if risk_mode == "Conservative":
    sl_mult, tp_mult = 1, 2
elif risk_mode == "Balanced":
    sl_mult, tp_mult = 1.5, 3
else:
    sl_mult, tp_mult = 2, 4

# ---------------- SL / TP ----------------
if signal == "BUY" and entry and atr:
    sl = entry - atr * sl_mult
    tp = entry + atr * tp_mult
elif signal == "SELL" and entry and atr:
    sl = entry + atr * sl_mult
    tp = entry - atr * tp_mult
else:
    sl, tp = None, None

# ---------------- HEADER ----------------
col1, col2, col3 = st.columns([5, 3, 2])
col1.markdown("### 🟡 OMI TERMINAL")
col2.markdown(f"### {session} SESSION")
col3.metric("📡 PRICE", current_price)

# ---------------- LAYOUT ----------------
left, right = st.columns([7, 3])

# ---------------- TRADINGVIEW CHART ----------------
with left:
    st.components.v1.html("""
    <div id="tv_chart"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({
        "width": "100%",
        "height": 600,
        "symbol": "OANDA:XAUUSD",
        "interval": "5",
        "timezone": "Asia/Kolkata",
        "theme": "light",
        "style": "1",
        "container_id": "tv_chart"
    });
    </script>
    """, height=600)

# ---------------- SIGNAL PANEL ----------------
with right:
    st.markdown("### SIGNAL")

    if signal == "BUY":
        st.success("🟢 BUY")
    elif signal == "SELL":
        st.error("🔴 SELL")
    else:
        st.warning("⚪ NO TRADE")

    # SOUND
    if sound_alert and signal in ["BUY", "SELL"]:
        if st.session_state.last_signal != signal:
            st.components.v1.html("""
                <audio autoplay>
                    <source src="https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3" type="audio/mp3">
                </audio>
            """, height=0)

    # METRICS
    st.markdown("### 📊 Trade Metrics")
    st.metric("📡 Current Price", current_price)
    st.metric("Confidence", round(prob, 2))
    st.metric("Entry", round(entry, 2) if entry else "--")
    st.metric("SL", round(sl, 2) if sl else "--")
    st.metric("TP", round(tp, 2) if tp else "--")

    # AI REASON
    st.markdown("### 🤖 OMI AI Reason")

    ema9 = df["ema9"].iloc[-1]
    ema21 = df["ema21"].iloc[-1]
    rsi = df["rsi"].iloc[-1]

    st.write("Trend:", "Bullish" if ema9 > ema21 else "Bearish")
    st.write("RSI:", round(rsi, 2))

    # DEBUG PANEL 🔥
    st.markdown("### 🧪 Debug Info")
    st.write({
        "Probability": prob,
        "EMA9": ema9,
        "EMA21": ema21,
        "RSI": rsi
    })

    # WHATSAPP ALERT
    if whatsapp_alert and signal in ["BUY", "SELL"] and phone_number:
        if st.session_state.last_signal != signal:

            msg = f"""
OMI Alert 🚀

Signal: {signal}
Entry: {round(entry,2)}
SL: {round(sl,2)}
TP: {round(tp,2)}

Confidence: {round(prob,2)}
Price: {current_price}
"""

            send_whatsapp(msg, phone_number)
            st.session_state.last_signal = signal
            st.success("WhatsApp Sent")

# ---------------- HISTORY ----------------
st.markdown("---")
st.markdown("### 📊 Signal History")

st.session_state.signal_history.append({
    "time": datetime.now().strftime("%H:%M:%S"),
    "signal": signal,
    "price": current_price,
    "confidence": round(prob, 2)
})

st.session_state.signal_history = st.session_state.signal_history[-20:]

hist_df = pd.DataFrame(st.session_state.signal_history)
st.dataframe(hist_df, use_container_width=True)

# ---------------- FOOTER ----------------
st.markdown(
    "<div style='text-align:right;color:gray;'>Powered by AEGIS</div>",
    unsafe_allow_html=True
)

# ---------------- AUTO REFRESH ----------------
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
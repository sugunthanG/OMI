import sys
import os
import glob

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
from datetime import datetime

# PIPELINE
from app.data import fetch_data
from app.features import create_features
from app.signals import generate_signal
from app.model import load_model
from app.whatsapp_api import send_whatsapp

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

# ---------------- MODEL AUTO DETECT ----------------
def get_available_models():
    files = glob.glob("models/gold_model_v*.pkl")
    files.sort(reverse=True)

    model_map = {}
    for f in files:
        name = os.path.basename(f)
        label = name.replace(".pkl", "").replace("gold_model_", "")
        model_map[label] = f

    if not model_map and os.path.exists("models/gold_model.pkl"):
        model_map["default"] = "models/gold_model.pkl"

    return model_map

MODEL_MAP = get_available_models()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## ⚙️ CONTROL PANEL")

    if not MODEL_MAP:
        st.error("No models found")
        st.stop()

    model_versions = list(MODEL_MAP.keys())

    # set default to v2 if exists
    default_index = 0
    for i, v in enumerate(model_versions):
        if v == "v2":
            default_index = i
            break

    model_version = st.selectbox(
        "🧠 Model Version",
        model_versions,
        index=default_index
    )

    # ✅ NOW set model path AFTER selection
    model_path = MODEL_MAP[model_version]

    st.caption(f"Using: {model_path}")

    st.markdown("---")

    auto_refresh = st.toggle("🔄 Auto Refresh", True)
    refresh_interval = st.slider("Refresh (sec)", 10, 120, 30)

    if st.button("🔁 Refresh Now"):
        st.rerun()

    st.markdown("---")

    timeframe = st.selectbox("🧠 Main Timeframe", ["5m", "15m", "1h"])

    st.markdown("---")

    # 🧠 RISK MODE
    risk_mode = st.radio(
        "⚡ Risk Mode",
        ["Conservative", "Balanced", "Aggressive"]
    )

    # 🔊 SOUND ALERT
    sound_alert = st.toggle("🔊 Sound Alert", False)

    st.markdown("---")

    

    # 📲 WHATSAPP ALERT
    whatsapp_alert = st.toggle("📲 WhatsApp Alert", False)

    phone_number = None
    if whatsapp_alert:
        phone_number = st.text_input("Enter WhatsApp Number", "+91XXXXXXXXXX")

    st.markdown("---")

    if st.button("🔁 Sync Model & Data"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.success("Synced!")
        st.rerun()

# ---------------- MODEL LOAD ----------------
@st.cache_resource
def get_model(path):
    try:
        return load_model(path)
    except Exception as e:
        st.error(f"Model Load Error: {e}")
        st.stop()

model = get_model(model_path)

# ---------------- SESSION ----------------
hour = datetime.utcnow().hour
session = "🌏 ASIAN" if hour < 8 else "🇬🇧 LONDON" if hour < 16 else "🇺🇸 NEW YORK"

# ---------------- DATA ----------------
@st.cache_data(ttl=30)
def get_tf_data(interval):
    df = fetch_data(interval=interval)
    if df is None or df.empty:
        return None

    df = create_features(df)
    df = df.sort_index()
    df.dropna(inplace=True)

    return df

# ---------------- SAFE SIGNAL ----------------
def safe_signal(df):
    try:
        return generate_signal(model, df)
    except Exception as e:
        print("Prediction Error:", e)
        return "NO TRADE", 0.0, None, None

# ---------------- MULTI TF ----------------
def get_signal_tf(interval):
    df = get_tf_data(interval)
    if df is None:
        return "NO DATA", 0.0

    sig, prob, _, _ = safe_signal(df)
    return sig, prob

tf5 = get_signal_tf("5m")
tf15 = get_signal_tf("15m")
tf1h = get_signal_tf("1h")

# ---------------- MAIN ----------------
df = get_tf_data(timeframe)

if df is None:
    st.error("No data available")
    st.stop()

signal, prob, entry, atr = safe_signal(df)

# ---------------- RISK MODE LOGIC ----------------
if risk_mode == "Conservative":
    sl_mult, tp_mult = 1.0, 2.0
elif risk_mode == "Balanced":
    sl_mult, tp_mult = 1.5, 3.0
else:  # Aggressive
    sl_mult, tp_mult = 2.0, 4.0

# ---------------- HEADER ----------------
col1, col2, col3 = st.columns([5, 3, 2])
col1.markdown("### 🟡 OMI TERMINAL")
col2.markdown(f"### {session}")
col3.success("🟢 LIVE")

# ---------------- LAYOUT ----------------
left, right = st.columns([7, 3])

# ---------------- CHART ----------------
with left:
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    ))
    fig.update_layout(template="plotly_dark", height=600)
    st.plotly_chart(fig, use_container_width=True)

# ---------------- SIGNAL PANEL ----------------
with right:
    st.markdown("### SIGNAL")

    if signal == "BUY":
        st.success("🟢 BUY")
    elif signal == "SELL":
        st.error("🔴 SELL")
    else:
        st.warning("⚪ NO TRADE")

    # 🔊 SOUND ALERT
    if sound_alert and signal in ["BUY", "SELL"]:
        st.audio("https://www.soundjay.com/buttons/sounds/beep-07.mp3")

    st.markdown("### 📊 Trade Metrics")
    st.metric("Confidence", round(prob, 2))

    if signal in ["BUY", "SELL"] and entry:
        st.metric("Entry Price", round(entry, 2))
    else:
        st.metric("Entry Price", "--")

    # SL TP
    if signal == "BUY" and entry and atr:
        sl = entry - atr * sl_mult
        tp = entry + atr * tp_mult
    elif signal == "SELL" and entry and atr:
        sl = entry + atr * sl_mult
        tp = entry - atr * tp_mult
    else:
        sl, tp = None, None

    if sl:
        st.metric("Stop Loss", round(sl, 2))
        st.metric("Take Profit", round(tp, 2))
    else:
        st.metric("Stop Loss", "--")
        st.metric("Take Profit", "--")

    # MULTI TF
    st.markdown("### 🧠 Multi Timeframe")

    def show_tf(name, data):
        sig, prob = data
        icon = "🟢" if sig == "BUY" else "🔴" if sig == "SELL" else "⚪"
        st.write(f"{name}: {icon} {sig} ({round(prob, 2)})")

    show_tf("5m", tf5)
    show_tf("15m", tf15)
    show_tf("1H", tf1h)

# ---------------- TRADE LOG ----------------
st.markdown("---")
st.markdown("### 📡 Trade Log")

log_df = pd.DataFrame({
    "Time": df.index[-10:],
    "Price": df["Close"].tail(10).values,
    "Signal": [signal]*10
})

st.dataframe(log_df, use_container_width=True, height=250)

# ---------------- FOOTER ----------------
st.markdown(
    "<div style='text-align:right;color:gray;'>Powered by AEGIS</div>",
    unsafe_allow_html=True
)

# ---------------- AUTO REFRESH ----------------
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
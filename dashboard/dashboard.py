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


# ============================================
#  AGREEMENT LOCK 
# ============================================

if "agreed" not in st.session_state:
    st.session_state.agreed = False

if not st.session_state.agreed:

    st.markdown("## 🚨 OMI TRADING AGREEMENT REQUIRED")

    st.warning("You must read and accept the trading rules before using OMI.")

    with st.expander("📘 Read Trading Rules & Ethics", expanded=True):
        st.markdown("""
### 📊 TRADING RULES & ETHICS

**1. Capital Protection**
- The trader shall prioritize capital preservation over profit generation.
- Maximum risk per trade shall not exceed 1–2% of total capital.
- Avoid excessive exposure that may lead to major drawdowns.

**2. Strategy Compliance**
- Trades must be executed strictly based on a predefined strategy.
- No trade shall be taken without a valid setup.
- Random or impulsive trading is strictly prohibited.

**3. Risk Management**
- Every trade must maintain a minimum Risk-to-Reward Ratio (RR) of 1:2.
- Stop Loss (SL) must be defined before entering any trade.
- Position sizing must follow risk management rules.

**4. Emotional Discipline**
- Maintain emotional control during trading.
- No revenge trading, FOMO, or fear-based decisions.
- All decisions must be logic-driven.

**5. Loss Acceptance**
- Losses are a natural part of trading.
- Avoid attempting to recover losses through irrational trades.
- Respect every trade outcome without emotional reaction.

**6. Trade Journal**
- Maintain a record of all trades.
- Include entry, exit, reasoning, and outcome.
- Review trades regularly for improvement.

**7. Trade Control**
- Avoid overtrading and unnecessary exposure.
- Execute only high-quality setups.
- Limit trades per session/day.

**8. Ethics**
- Maintain integrity and honesty in trading.
- No market manipulation or unethical practices.
- Follow fair trading standards.

**9. Continuous Learning**
- Commit to continuous improvement.
- Learn from mistakes and refine strategies.
- Stay updated with market behavior.

**10. Consistency**
- Focus on long-term consistency over short-term profits.
- Follow a disciplined and repeatable process.
- Stick to rules regardless of outcomes.

**11. Pre-Trade Checklist**
- Confirm valid setup before entering.
- Define Entry, Stop Loss (SL), and Take Profit (TP).
- No trade without full validation.

**12. Accountability**
- Take full responsibility for all trading decisions.
- Do not blame external factors.
- Maintain discipline and self-evaluation.
        """)

    agree = st.checkbox(" I have read and agree to the rules")

    if st.button("ENTER OMI TERMINAL"):
        if agree:
            st.session_state.agreed = True
            st.rerun()
        else:
            st.error("You must accept the rules to continue")

    st.stop()

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

# ---------------- CAPITAL TRACKING ----------------
if "capital" not in st.session_state:
    st.session_state.capital = 10000

if "equity_curve" not in st.session_state:
    st.session_state.equity_curve = []

if "trade_results" not in st.session_state:
    st.session_state.trade_results = []


# ---------------- CALCULATE PnL ----------------
for trade in st.session_state.active_trades:

    if trade["status"] in ["WIN", "LOSS"] and trade["pnl"] == 0:

        risk_per_trade = 0.02 * st.session_state.capital

        if trade["status"] == "WIN":
            profit = risk_per_trade * 2
            trade["pnl"] = profit
            st.session_state.capital += profit

        elif trade["status"] == "LOSS":
            loss = -risk_per_trade
            trade["pnl"] = loss
            st.session_state.capital += loss

        st.session_state.trade_results.append(trade["pnl"])


# ---------------- EQUITY UPDATE ----------------
st.session_state.equity_curve.append(st.session_state.capital)
st.session_state.equity_curve = st.session_state.equity_curve[-100:]


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
            "signal": signal,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "status": "OPEN",
            "pnl": 0,
            "time": datetime.now().strftime("%H:%M:%S")
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

# ---------------- ACCOUNT PERFORMANCE ----------------
st.markdown("### 💰 Account Performance")

col1, col2, col3 = st.columns(3)

total_pnl = sum(st.session_state.trade_results)
total_trades = len(st.session_state.trade_results)

avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

col1.metric("💰 Capital", round(st.session_state.capital, 2))
col2.metric("📈 Total PnL", round(total_pnl, 2))
col3.metric("⚖️ Avg Trade", round(avg_pnl, 2))


# ---------------- EQUITY CURVE ----------------
st.markdown("### 📈 Equity Curve")

if len(st.session_state.equity_curve) > 1:
    equity_df = pd.DataFrame({
        "Equity": st.session_state.equity_curve
    })
    st.line_chart(equity_df)
else:
    st.info("Not enough data for equity curve")

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
# =========================================
# OMI DASHBOARD (FINAL V12 - PRO)
# =========================================

import sys, os, glob, time
from datetime import datetime, UTC

import streamlit as st
import pandas as pd

# ---------------- PATH SETUP ----------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ---------------- IMPORTS ----------------
from app.login import login, logout
from app.data import fetch_data
from app.features import create_features
from app.signals import generate_signal, FEATURES
from app.model import load_model
from app.whatsapp_api import send_whatsapp
from app.backtester import run_backtest
from app.trade_tracker import update_trades


# # 🔐 LOGIN CHECK
# if not login():
#     st.stop()

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

def run_dashboard():
   

    


    st.markdown("""
    <style>

    /* ===== GLOBAL ===== */
    body {
        background: linear-gradient(135deg, #0b0f1a, #0e1117);
        color: #e5e7eb;
        font-family: 'Inter', sans-serif;
    }

    /* remove top spacing */
    .block-container {
        padding-top: 1rem;
    }

    /* ===== GLASS CARD ===== */
    .card {
        background: rgba(17, 24, 39, 0.6);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);

        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;

        padding: 20px;
        margin-bottom: 12px;

        box-shadow: 
            0 8px 30px rgba(0, 0, 0, 0.6),
            inset 0 0 0.5px rgba(255,255,255,0.1);
    }

    /* hover animation */
    .card:hover {
        transform: translateY(-4px) scale(1.01);
        transition: all 0.25s ease;
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.8),
            0 0 20px rgba(59,130,246,0.15);
    }

    /* ===== SIGNAL BOX ===== */
    .signal-box {
        padding: 22px;
        border-radius: 14px;
        text-align: center;
        font-size: 30px;
        font-weight: 700;
        letter-spacing: 1px;

        backdrop-filter: blur(10px);
    }

    /* BUY */
    .buy {
        background: linear-gradient(135deg, #16a34a, #22c55e);
        box-shadow: 0 0 25px rgba(34,197,94,0.6);
    }

    /* SELL */
    .sell {
        background: linear-gradient(135deg, #dc2626, #ef4444);
        box-shadow: 0 0 25px rgba(239,68,68,0.6);
    }

    /* NO TRADE */
    .no {
        background: linear-gradient(135deg, #374151, #4b5563);
        box-shadow: 0 0 15px rgba(107,114,128,0.4);
    }

    /* ===== METRIC TEXT ===== */
    h1, h2, h3 {
        color: #f9fafb;
    }

    /* ===== SMALL LABELS ===== */
    label, .stMetric label {
        color: #9ca3af !important;
    }

    /* ===== VALUE TEXT ===== */
    .stMetric div {
        color: #f3f4f6 !important;
        font-weight: 600;
    }

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background: #374151;
        border-radius: 10px;
    }

    /* ===== GLOW TEXT (OPTIONAL) ===== */
    .glow-green {
        color: #22c55e;
        text-shadow: 0 0 10px rgba(34,197,94,0.7);
    }

    .glow-red {
        color: #ef4444;
        text-shadow: 0 0 10px rgba(239,68,68,0.7);
    }

    </style>
    """, unsafe_allow_html=True)

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


    # =========================================
    # SESSION INIT
    # =========================================
    def init():
        defaults = {
            "last_signal": None,
            "signal_history": [],
            "active_trades": [],
            "capital": 10000,
            "equity_curve": [],
            "trade_results": []
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    init()

    # =========================================
    # MODEL
    # =========================================
    def get_models():
        files = sorted(glob.glob("models/gold_model_v*.pkl"), reverse=True)
        return {os.path.basename(f): f for f in files}


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
    MODEL_PATH = "models/gold_model_v2.pkl"

    if not os.path.exists(MODEL_PATH):
        st.error(f"Model not found at: {MODEL_PATH}")
        st.stop()

    @st.cache_resource
    def get_model():
        return load_model(MODEL_PATH)

    model = get_model()

    st.caption(f"Using: {MODEL_PATH}")
    st.markdown("---")


    # =========================
    # ⚙️ SIDEBAR
    # =========================
    def sidebar_controls():
        with st.sidebar:
            st.markdown("## ⚙️ CONTROL PANEL")
            logout()

            if not  MODEL_PATH:
                st.error("No models found")
                st.stop()

            versions = list( MODEL_PATH.keys())
            default_idx = versions.index("v2") if "v2" in versions else 0

            model_version = st.selectbox("🧠 Model Version", versions, index=default_idx)
            model_path =  MODEL_PATH[model_version]

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


            if st.button("➕ Create ID"):
                st.warning("🚧 ID Creation Feature will be Enabling coming soon")

        return model_path, timeframe, risk_mode, sound_alert, whatsapp_alert, phone, auto_refresh, refresh_interval

    model_path, timeframe, risk_mode, sound_alert, whatsapp_alert, phone, auto_refresh, refresh_interval = sidebar_controls()
    model = get_model(model_path)


    # =========================================
    # DATA
    # =========================================
    df = fetch_data()
    df = create_features(df)

    for f in FEATURES:
        if f not in df.columns:
            df[f] = 0

    df = df.dropna()

    # =========================================
    # SIGNAL
    # =========================================
    signal, prob, entry, atr = generate_signal(model, df)

    # FILTER LOW QUALITY
    if prob < 0.65:
        signal = "NO TRADE"

    price = float(df["Close"].iloc[-1])
    current_price = round(float(df["Close"].iloc[-1]), 2)

    # =========================================
    # RISK
    # =========================================
    if signal == "BUY":
        sl = entry - atr * 1.5
        tp = entry + atr * 3
    elif signal == "SELL":
        sl = entry + atr * 1.5
        tp = entry - atr * 3
    else:
        sl, tp = None, None

    # =========================================
    # HEADER
    # =========================================


    st.markdown("## 🟡 OMI TERMINAL")

    col1, col2, col3 = st.columns(3)

    # 💰 PRICE
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 💰 Price")
        st.markdown(f"## {current_price}")
        st.markdown('</div>', unsafe_allow_html=True)

    # 🌍 SESSION
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🌍 Session")
        st.markdown(f"## {session}")
        st.markdown('</div>', unsafe_allow_html=True)

    # 📡 SIGNAL + CONFIDENCE
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📡 Signal")

        if signal == "BUY":
            st.markdown('<div class="signal-box buy glow-green">🟢 BUY</div>', unsafe_allow_html=True)
        elif signal == "SELL":
            st.markdown('<div class="signal-box sell glow-red">🔴 SELL</div>', unsafe_allow_html=True)
        else:
            st.markdown("## ⚪ NO TRADE")

        st.markdown(f"**🎯 Confidence:** {round(prob, 2)}")
        st.markdown('</div>', unsafe_allow_html=True)

    # =========================
    # 📊 LAYOUT
    # =========================
    left, right = st.columns([7, 3])

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        st.components.v1.html("""
        <script src="https://s3.tradingview.com/tv.js"></script>
        <div id="tv_chart"></div>
        <script>
        new TradingView.widget({
            width: "100%",
            height: 500,
            symbol: "OANDA:XAUUSD",
            interval: "5",
            timezone: "Asia/Kolkata",
            theme: "light",
            style: "1",
            container_id: "tv_chart"
        });
        </script>
        """, height=520)

        st.markdown('</div>', unsafe_allow_html=True)


    with right:
        

        # 🔊 Sound Alert
        if sound_alert and signal in ["BUY", "SELL"] and st.session_state.last_signal != signal:
            st.components.v1.html("""
            <audio autoplay>
                <source src=\"https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3\">
            </audio>
            """, height=0)

        # 📊 Metrics
        st.markdown('<div class="card">', unsafe_allow_html=True)

        st.markdown("### 📊 Trade Metrics")
        
        st.metric("Confidence", round(prob, 2))
        st.metric("Entry", round(entry, 2) if entry else "--")
        st.metric("SL", round(sl, 2) if sl else "--")
        st.metric("TP", round(tp, 2) if tp else "--")

        st.markdown('</div>', unsafe_allow_html=True)

        # 🤖 AI Reason
        ema9 = df["ema9"].iloc[-1] if "ema9" in df.columns else None
        ema21 = df["ema21"].iloc[-1] if "ema21" in df.columns else None
        rsi = df["rsi"].iloc[-1] if "rsi" in df.columns else None

        st.markdown("### 🤖 OMI AI Reason")
        if ema9 is not None and ema21 is not None:
            trend = "Bullish" if ema9 > ema21 else "Bearish"
        else:
            trend = "No Data"

        st.write(
        "Trend:",
        "Bullish" if (ema9 is not None and ema21 is not None and ema9 > ema21)
        else "Bearish" if (ema9 is not None and ema21 is not None)
        else "No Data"
        )
        st.write("RSI:", round(rsi, 2))

        st.markdown("### 🧪 Debug Info")
        st.write({"Confidence": prob, "EMA9": ema9, "EMA21": ema21, "RSI": rsi})

        # 📲 WhatsApp
        if whatsapp_alert and signal in ["BUY", "SELL"] and phone and st.session_state.last_signal != signal:
            msg = f"""Hey User 👋\n\nSignal: {signal}\nEntry: {round(entry,2)}\nSL: {round(sl,2)}\nTP: {round(tp,2)}\nConfidence: {round(prob,2)}\n"""
            send_whatsapp(msg, phone)
            st.session_state.last_signal = signal
            st.success("WhatsApp Sent")


    # =========================================
    # SIGNAL QUALITY
    # =========================================
    if prob >= 0.75:
        st.success("🔥 Strong Signal")
    elif prob >= 0.65:
        st.warning("⚡ Medium Signal")
    else:
        st.info("❄️ Weak Signal")

    # =========================================
    # TRADE CREATE
    # =========================================
    st.session_state.active_trades = update_trades(st.session_state.active_trades, df)

    if signal in ["BUY", "SELL"] and sl and tp:

        open_same = any(
            t["status"] == "OPEN" and t["signal"] == signal
            for t in st.session_state.active_trades
        )

        if not open_same:

            st.session_state.active_trades.append({
                "signal": signal,
                "entry": entry,
                "sl": sl,
                "tp": tp,
                "atr": atr,
                "confidence": prob,
                "status": "OPEN",
                "pnl": 0,
                "open_index": len(df),
                "open_time": datetime.now()
            })

    # =========================================
    # PNL UPDATE
    # =========================================
    for trade in st.session_state.active_trades:

        if trade["status"] in ["WIN", "LOSS"] and trade["pnl"] == 0:

            risk = 0.02 * st.session_state.capital

            if trade["status"] == "WIN":
                pnl = risk * 2
            else:
                pnl = -risk

            trade["pnl"] = pnl
            st.session_state.capital += pnl
            st.session_state.trade_results.append(pnl)

    # =========================================
    # EQUITY
    # =========================================
    st.session_state.equity_curve.append(st.session_state.capital)
    st.session_state.equity_curve = st.session_state.equity_curve[-100:]

    # =========================================
    # DISPLAY TRADES
    # =========================================
    st.subheader("📊 Trades")

    trades = pd.DataFrame(st.session_state.active_trades)

    if not trades.empty:

        wins = len(trades[trades.status == "WIN"])
        losses = len(trades[trades.status == "LOSS"])

        winrate = (wins / (wins + losses) * 100) if (wins + losses) else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Wins", wins)
        c2.metric("Losses", losses)
        c3.metric("Winrate", round(winrate, 2))

        st.dataframe(trades.tail(20))

    # =========================================
    # EQUITY CURVE
    # =========================================
    st.subheader("📈 Equity")

    if len(st.session_state.equity_curve) > 1:
        st.line_chart(st.session_state.equity_curve)

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




    # =========================================
    # SIGNAL HISTORY
    # =========================================
    st.session_state.signal_history.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "signal": signal,
        "price": price,
        "confidence": prob
    })

    st.session_state.signal_history = st.session_state.signal_history[-20:]

    st.subheader("📜 Signal History")
    st.dataframe(pd.DataFrame(st.session_state.signal_history))


    # =========================
    # 🧾 FOOTER
    # =========================
    st.markdown("<div style='text-align:right;color:gray;'>Powered by AEGIS</div>", unsafe_allow_html=True)

    # =========================================
    # AUTO REFRESH
    # =========================================
    if auto_refresh:
        st.caption(f"Auto refresh every {refresh_interval}s")
        st.autorefresh(interval=refresh_interval * 1000, key="refresh")

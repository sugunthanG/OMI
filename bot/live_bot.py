# =========================================
# LIVE BOT (V2 - PRO SYSTEM)
# =========================================

import time
from datetime import datetime

from app.model import load_model
from app.data import fetch_data
from app.features import create_features
from app.signals import generate_signal
from app.trade_tracker import update_trades
from app.whatsapp_api import send_whatsapp
from app.config import PHONE_NUMBERS

# ================= LOAD =================
model = load_model()

# ================= STATE =================
open_trades = []
last_trade_time = None

MAX_TRADES = 3
COOLDOWN = 2  # candles


# =========================================
# MAIN LOOP
# =========================================
while True:

    print("\n⏳ Checking market...")

    try:
        df = fetch_data()
        df = create_features(df)

        # ================= UPDATE EXISTING TRADES =================
        open_trades = update_trades(open_trades, df)

        # Remove closed trades (optional keep history separately)
        open_trades = [t for t in open_trades if t["status"] == "OPEN"]

        print(f"📊 Open Trades: {len(open_trades)}")

        # ================= SIGNAL =================
        signal, prob, entry, atr = generate_signal(model, df)

        print("Signal:", signal, "| Confidence:", round(prob, 2))

        # ================= FILTER =================
        if signal == "NO TRADE" or atr is None:
            print("⚪ NO TRADE")
            time.sleep(300)
            continue

        # Limit trades
        if len(open_trades) >= MAX_TRADES:
            print("⚠️ Max trades reached")
            time.sleep(300)
            continue

        # Cooldown control
        if last_trade_time is not None:
            if len(df) - last_trade_time < COOLDOWN:
                print("⏳ Cooldown active")
                time.sleep(300)
                continue

        # ================= CREATE TRADE =================
        if signal == "BUY":
            sl = entry - atr * 1.5
            tp = entry + atr * 3
        else:
            sl = entry + atr * 1.5
            tp = entry - atr * 3

        trade = {
            "signal": signal,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "atr": atr,
            "confidence": prob,
            "status": "OPEN",
            "open_index": len(df),
            "open_time": datetime.now()
        }

        open_trades.append(trade)
        last_trade_time = len(df)

        # ================= ALERT =================
        msg = f"""
🚀 {signal} GOLD

Entry: {round(entry,2)}
SL: {round(sl,2)}
TP: {round(tp,2)}

Confidence: {round(prob,2)}
Open Trades: {len(open_trades)}
"""

        for num in PHONE_NUMBERS:
            send_whatsapp(msg, num)

        print("✅ Trade Executed")

    except Exception as e:
        print("❌ ERROR:", e)

    time.sleep(300)
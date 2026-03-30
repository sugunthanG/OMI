import time
from app.model import load_model
from app.data import fetch_data
from app.features import create_features
from app.signals import generate_signal
from app.whatsapp_api import send_whatsapp
from app.config import PHONE_NUMBERS

model = load_model()

last_signal = None

while True:

    print("⏳ Checking market...")

    try:
        df = fetch_data()
        df = create_features(df)

        signal, prob, entry, atr = generate_signal(model, df)

        print("Signal:", signal, "| Confidence:", round(prob,2))

        if signal != "NO TRADE" and signal != last_signal:

            if signal == "BUY":
                sl = entry - atr * 1.5
                tp = entry + atr * 3
            else:
                sl = entry + atr * 1.5
                tp = entry - atr * 3

            msg = f"""
{signal} GOLD
Entry: {round(entry,2)}
SL: {round(sl,2)}
TP: {round(tp,2)}
Confidence: {round(prob,2)}
"""

            for num in PHONE_NUMBERS:
                send_whatsapp(msg, num)

            last_signal = signal

        else:
            print("⚪ NO TRADE")

    except Exception as e:
        print("❌ ERROR:", e)

    time.sleep(300)
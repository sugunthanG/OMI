# =========================================
# SIGNAL GENERATION (V2 - MULTI CLASS FIX)
# =========================================

FEATURES = [
    'ema9','ema21','ema50','rsi','atr','body','momentum',   
    'ema_ratio','price_above_ema','rsi_change','atr_ratio',
    'high_break','low_break','bullish'
]

# 🔥 Confidence threshold (avoid weak signals)
CONF_THRESHOLD = 0.60


def generate_signal(model, df):

    # ================= INPUT =================
    latest = df[FEATURES].iloc[-1:]

    # ================= PREDICTION =================
    probs = model.predict_proba(latest)[0]
    pred_class = model.predict(latest)[0]

    # Confidence = highest probability
    confidence = float(max(probs))

    # ================= PRICE =================
    entry = float(df["Close"].iloc[-1])
    atr = float(df["atr"].iloc[-1]) if "atr" in df else None

    # ================= FILTERS =================
    ema9 = df["ema9"].iloc[-1]
    ema21 = df["ema21"].iloc[-1]
    rsi = df["rsi"].iloc[-1]

    trend_up = ema9 > ema21
    trend_down = ema9 < ema21

    # ================= SIGNAL LOGIC =================
    if confidence < CONF_THRESHOLD:
        signal = "NO TRADE"

    else:
        if pred_class == 2 and trend_up and rsi < 70:
            signal = "BUY"

        elif pred_class == 0 and trend_down and rsi > 30:
            signal = "SELL"

        else:
            signal = "NO TRADE"

    return signal, confidence, entry, atr
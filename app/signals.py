# =========================================
# SIGNAL GENERATION (V12 - CORRECT)
# =========================================

FEATURES = [
    'ema20','ema50','rsi','atr',
    'momentum','trend_up','trend_down',
    'break_up','break_down'
]

# ================= CONFIG =================
CONF_THRESHOLD = 0.65   # strong filter


# =========================================
# MAIN SIGNAL FUNCTION
# =========================================
def generate_signal(model, df):

    try:
        # ================= INPUT =================
        latest = df[FEATURES].iloc[-1:].copy()

        # ================= MODEL =================
        probs = model.predict_proba(latest)[0]

        sell_prob = float(probs[0])
        hold_prob = float(probs[1])
        buy_prob = float(probs[2])

        confidence = float(max(probs))

        # ================= PRICE =================
        entry = float(df["Close"].iloc[-1])
        atr = float(df["atr"].iloc[-1])

        trend_up = int(df["trend_up"].iloc[-1])
        trend_down = int(df["trend_down"].iloc[-1])

        # ================= DEFAULT =================
        signal = "NO TRADE"

        # ================= CONFIDENCE FILTER =================
        if confidence < CONF_THRESHOLD:
            return signal, confidence, entry, atr

        # ================= MODEL DECISION =================
        pred_class = probs.argmax()

        # ================= BUY =================
        if pred_class == 2 and trend_up == 1:
            signal = "BUY"

        # ================= SELL =================
        elif pred_class == 0 and trend_down == 1:
            signal = "SELL"

        return signal, confidence, entry, atr

    except Exception as e:
        print(f"Signal Error: {e}")
        return "NO TRADE", 0.0, None, None
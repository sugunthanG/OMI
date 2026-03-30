from app.config import BUY_THRESHOLD, SELL_THRESHOLD

FEATURES = [
    'ema50','atr','macd','body','momentum',
    'ema_trend','trend_strength','rsi_zone',
    'volatility','ema9','ema21','rsi','range','Close'
]

def generate_signal(model, df):

    # ✅ USE ONLY TRAINED FEATURES
    latest = df[FEATURES].iloc[-1:]

    # ✅ MODEL PROBABILITY
    prob = model.predict_proba(latest)[0][1]

    # PRICE + ATR
    entry = float(df["Close"].iloc[-1])
    atr = float(df["atr"].iloc[-1]) if "atr" in df else None

    # ✅ TREND FILTER
    ema9 = df["ema9"].iloc[-1]
    ema21 = df["ema21"].iloc[-1]

    # ✅ RSI FILTER
    rsi = df["rsi"].iloc[-1]

    # 🔥 FINAL LOGIC
    if prob >= BUY_THRESHOLD and ema9 > ema21 and rsi < 70:
        signal = "BUY"

    elif prob <= SELL_THRESHOLD and ema9 < ema21 and rsi > 30:
        signal = "SELL"

    else:
        signal = "NO TRADE"

    return signal, prob, entry, atr
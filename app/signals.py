from app.config import BUY_THRESHOLD, SELL_THRESHOLD

FEATURES = [
    'ema50',
    'atr',
    'macd',
    'body',
    'momentum',
    'ema_trend',
    'trend_strength',
    'rsi_zone',
    'volatility',
    'ema9',
    'ema21',
    'rsi',
    'range',
    'Close'
]

def generate_signal(model, df):

    latest = df.tail(1)

    prob = model.predict_proba(latest[FEATURES])[0][1]

    entry = latest['Close'].values[0]
    atr = latest['atr'].values[0]
    ema9 = latest['ema9'].values[0]
    ema21 = latest['ema21'].values[0]
    rsi = latest['rsi'].values[0]

    signal = "NO TRADE"

    # STRONG BUY
    if prob > BUY_THRESHOLD and ema9 > ema21 and rsi < 65:
        signal = "BUY"

    # STRONG SELL
    elif prob < SELL_THRESHOLD and ema9 < ema21 and rsi > 35:
        signal = "SELL"

    return signal, prob, entry, atr
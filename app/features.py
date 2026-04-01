# =========================================
# FEATURE ENGINEERING (V2 MATCH)
# =========================================

import ta

def create_features(df):

    # ================= BASIC =================
    df['ema9'] = ta.trend.ema_indicator(df['Close'], 9)
    df['ema21'] = ta.trend.ema_indicator(df['Close'], 21)
    df['ema50'] = ta.trend.ema_indicator(df['Close'], 50)

    df['rsi'] = ta.momentum.rsi(df['Close'], 14)

    df['atr'] = ta.volatility.average_true_range(
        df['High'], df['Low'], df['Close'], 14
    )

    df['body'] = abs(df['Close'] - df['Open'])
    df['momentum'] = df['Close'] - df['Close'].shift(5)

    # ================= NEW FEATURES (CRITICAL) =================
    df['ema_ratio'] = df['ema9'] / df['ema21']
    df['price_above_ema'] = (df['Close'] > df['ema21']).astype(int)
    df['rsi_change'] = df['rsi'].diff()
    df['atr_ratio'] = df['atr'] / df['Close']

    df['high_break'] = (df['Close'] > df['High'].shift(10)).astype(int)
    df['low_break'] = (df['Close'] < df['Low'].shift(10)).astype(int)

    df['bullish'] = (df['Close'] > df['Open']).astype(int)

    # ================= CLEAN =================
    df.dropna(inplace=True)

    return df
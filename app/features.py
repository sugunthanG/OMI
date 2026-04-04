# =========================================
# FEATURE ENGINEERING (V12 - MATCH MODEL)
# =========================================

import ta

def create_features(df):

    # ================= BASIC =================
    df['ema20'] = ta.trend.ema_indicator(df['Close'], 20)
    df['ema50'] = ta.trend.ema_indicator(df['Close'], 50)

    df['rsi'] = ta.momentum.rsi(df['Close'], 14)

    df['atr'] = ta.volatility.average_true_range(
        df['High'], df['Low'], df['Close'], 14
    )

    # ================= MOMENTUM =================
    df['momentum'] = df['Close'] - df['Close'].shift(10)

    # ================= BREAKOUT =================
    df['hh_20'] = df['High'].rolling(20).max()
    df['ll_20'] = df['Low'].rolling(20).min()

    df['break_up'] = (df['Close'] > df['hh_20'].shift(1)).astype(int)
    df['break_down'] = (df['Close'] < df['ll_20'].shift(1)).astype(int)

    # ================= TREND =================
    df['trend_up'] = (df['ema20'] > df['ema50']).astype(int)
    df['trend_down'] = (df['ema20'] < df['ema50']).astype(int)

    # ================= CLEAN =================
    df.dropna(inplace=True)

    return df
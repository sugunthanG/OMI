import pandas as pd
import numpy as np

def create_features(df):
    df = df.copy()

    # BASIC
    df['body'] = df['Close'] - df['Open']
    df['range'] = df['High'] - df['Low']

    # EMA
    df['ema9'] = df['Close'].ewm(span=9).mean()
    df['ema21'] = df['Close'].ewm(span=21).mean()
    df['ema50'] = df['Close'].ewm(span=50).mean()

    # TREND
    df['ema_trend'] = np.where(df['ema9'] > df['ema21'], 1, -1)
    df['trend_strength'] = abs(df['ema9'] - df['ema21'])

    # RSI
    delta = df['Close'].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / (avg_loss + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))

    df['rsi_zone'] = np.where(df['rsi'] > 60, 1,
                        np.where(df['rsi'] < 40, -1, 0))

    # ATR
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()

    # MACD
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['macd'] = ema12 - ema26

    # MOMENTUM
    df['momentum'] = df['Close'] - df['Close'].shift(4)

    # VOLATILITY
    df['volatility'] = df['Close'].rolling(10).std()

    df = df.dropna()

    return df
# =========================================
# BACKTEST ENGINE
# =========================================

import pandas as pd

def run_backtest(df, model, generate_signal):

    trades = []

    for i in range(50, len(df) - 10):  # skip early rows
        sub_df = df.iloc[:i].copy()

        signal, confidence, entry, atr = generate_signal(model, sub_df)

        if signal == "NO TRADE" or atr is None:
            continue

        price = entry

        # SL / TP
        if signal == "BUY":
            sl = price - atr
            tp = price + (atr * 2)
        else:
            sl = price + atr
            tp = price - (atr * 2)

        future = df.iloc[i:i+10]

        result = "LOSS"

        for _, row in future.iterrows():
            high = row["High"]
            low = row["Low"]

            if signal == "BUY":
                if low <= sl:
                    result = "LOSS"
                    break
                if high >= tp:
                    result = "WIN"
                    break

            elif signal == "SELL":
                if high >= sl:
                    result = "LOSS"
                    break
                if low <= tp:
                    result = "WIN"
                    break

        trades.append({
            "signal": signal,
            "entry": price,
            "sl": sl,
            "tp": tp,
            "confidence": confidence,
            "result": result
        })

    trades_df = pd.DataFrame(trades)

    if trades_df.empty:
        return trades_df, {}

    win_rate = (trades_df["result"] == "WIN").mean()

    stats = {
        "total_trades": len(trades_df),
        "wins": int((trades_df["result"] == "WIN").sum()),
        "losses": int((trades_df["result"] == "LOSS").sum()),
        "win_rate": round(win_rate * 100, 2)
    }

    return trades_df, stats
# =========================================
# BACKTEST ENGINE (V2 - REALISTIC)
# =========================================

import pandas as pd


def run_backtest(df, model, generate_signal):

    trades = []

    balance = 1000   # starting capital
    risk_per_trade = 0.02  # 2% risk

    for i in range(100, len(df) - 15):  # more safe start
        sub_df = df.iloc[:i].copy()

        signal, confidence, entry, atr = generate_signal(model, sub_df)

        # ================= FILTER =================
        if signal == "NO TRADE" or atr is None:
            continue

        if confidence < 0.65:   # 🔥 IMPORTANT
            continue

        price = entry

        # ================= SL / TP =================
        rr = 2  # risk reward

        if signal == "BUY":
            sl = price - atr
            tp = price + (atr * rr)
        else:
            sl = price + atr
            tp = price - (atr * rr)

        # ================= POSITION SIZE =================
        risk_amount = balance * risk_per_trade
        lot = risk_amount / atr if atr != 0 else 0

        future = df.iloc[i:i+15]

        result = "LOSS"
        exit_price = price

        # ================= TRADE SIMULATION =================
        for _, row in future.iterrows():
            high = row["High"]
            low = row["Low"]

            if signal == "BUY":

                if low <= sl:
                    result = "LOSS"
                    exit_price = sl
                    break

                if high >= tp:
                    result = "WIN"
                    exit_price = tp
                    break

            elif signal == "SELL":

                if high >= sl:
                    result = "LOSS"
                    exit_price = sl
                    break

                if low <= tp:
                    result = "WIN"
                    exit_price = tp
                    break

        # ================= PNL =================
        if result == "WIN":
            profit = risk_amount * rr
            balance += profit
        else:
            loss = risk_amount
            balance -= loss

        trades.append({
            "signal": signal,
            "entry": price,
            "sl": sl,
            "tp": tp,
            "confidence": confidence,
            "result": result,
            "balance": balance
        })

    trades_df = pd.DataFrame(trades)

    if trades_df.empty:
        return trades_df, {}

    win_rate = (trades_df["result"] == "WIN").mean()

    stats = {
        "total_trades": len(trades_df),
        "wins": int((trades_df["result"] == "WIN").sum()),
        "losses": int((trades_df["result"] == "LOSS").sum()),
        "win_rate": round(win_rate * 100, 2),
        "final_balance": round(balance, 2),
        "profit": round(balance - 1000, 2)
    }

    return trades_df, stats
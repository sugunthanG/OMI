# =========================================
# REAL-TIME TRADE TRACKER
# =========================================

def update_trades(trades, df):
    """
    Update open trades using latest candle
    """

    if not trades:
        return trades

    latest = df.iloc[-1]
    high = latest["High"]
    low = latest["Low"]

    for trade in trades:
        if trade["status"] != "OPEN":
            continue

        if trade["signal"] == "BUY":
            if low <= trade["sl"]:
                trade["status"] = "LOSS"
            elif high >= trade["tp"]:
                trade["status"] = "WIN"

        elif trade["signal"] == "SELL":
            if high >= trade["sl"]:
                trade["status"] = "LOSS"
            elif low <= trade["tp"]:
                trade["status"] = "WIN"

    return trades
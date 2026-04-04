# =========================================
# REAL-TIME TRADE TRACKER (V2 - ADVANCED)
# =========================================

from datetime import datetime

def update_trades(trades, df):
    """
    Update open trades using latest candle
    """

    if not trades or df.empty:
        return trades

    latest = df.iloc[-1]
    high = latest["High"]
    low = latest["Low"]
    current_price = latest["Close"]

    for trade in trades:

        if trade["status"] != "OPEN":
            continue

        # ================= TIMEOUT (VERY IMPORTANT) =================
        if "open_index" in trade:
            if len(df) - trade["open_index"] > 20:
                trade["status"] = "CLOSED"
                trade["exit_price"] = current_price
                trade["exit_reason"] = "TIMEOUT"
                continue

        # ================= BREAK-EVEN LOGIC =================
        if trade["signal"] == "BUY":
            if current_price > trade["entry"] + (trade["atr"] * 0.5):
                trade["sl"] = max(trade["sl"], trade["entry"])

        elif trade["signal"] == "SELL":
            if current_price < trade["entry"] - (trade["atr"] * 0.5):
                trade["sl"] = min(trade["sl"], trade["entry"])

        # ================= EXIT LOGIC =================
        if trade["signal"] == "BUY":

            if low <= trade["sl"]:
                trade["status"] = "LOSS"
                trade["exit_price"] = trade["sl"]
                trade["exit_reason"] = "SL"

            elif high >= trade["tp"]:
                trade["status"] = "WIN"
                trade["exit_price"] = trade["tp"]
                trade["exit_reason"] = "TP"

        elif trade["signal"] == "SELL":

            if high >= trade["sl"]:
                trade["status"] = "LOSS"
                trade["exit_price"] = trade["sl"]
                trade["exit_reason"] = "SL"

            elif low <= trade["tp"]:
                trade["status"] = "WIN"
                trade["exit_price"] = trade["tp"]
                trade["exit_reason"] = "TP"

        # ================= SAVE CLOSE TIME =================
        if trade["status"] != "OPEN":
            trade["close_time"] = datetime.now()

    return trades
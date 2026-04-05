from tvDatafeed import TvDatafeed, Interval
import time

# ✅ NO LOGIN → NO CHROMEDRIVER NEEDED
tv = TvDatafeed()

def fetch_data(interval="5m"):

    if interval == "5m":
        tf = Interval.in_5_minute
    elif interval == "15m":
        tf = Interval.in_15_minute
    else:
        tf = Interval.in_1_hour

    for attempt in range(3):  # retry 3 times
        try:
            df = tv.get_hist(
                symbol="XAUUSD",
                exchange="OANDA",
                interval=tf,
                n_bars=500
            )

            if df is not None and not df.empty:
                df.rename(columns={
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume"
                }, inplace=True)

                # ✅ Indicators
                df["ema9"] = df["Close"].ewm(span=9).mean()
                df["ema15"] = df["Close"].ewm(span=15).mean()

                return df

        except Exception as e:
            print("Retrying fetch...", e)
            time.sleep(2)

    return None
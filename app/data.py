from tvDatafeed import TvDatafeed, Interval

tv = TvDatafeed()

def fetch_data(interval="5m"):

    if interval == "5m":
        tf = Interval.in_5_minute
    elif interval == "15m":
        tf = Interval.in_15_minute
    else:
        tf = Interval.in_1_hour

    df = tv.get_hist(
        symbol="XAUUSD",
        exchange="OANDA",
        interval=tf,
        n_bars=500
    )

    if df is None or df.empty:
        return None

    df.rename(columns={
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume"
    }, inplace=True)

    return df
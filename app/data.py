# =========================================
# OMI DATA FETCH (CLOUD SAFE VERSION)
# =========================================

from tvDatafeed import TvDatafeed, Interval
import time
import threading
import pandas as pd
import yfinance as yf

# ✅ Initialize TV (no login)
tv = TvDatafeed()


# =========================
# 🔁 MAIN FETCH FUNCTION
# =========================
def fetch_data(interval="5m"):

    if interval == "5m":
        tf = Interval.in_5_minute
    elif interval == "15m":
        tf = Interval.in_15_minute
    else:
        tf = Interval.in_1_hour

    for attempt in range(3):
        try:
            print("📡 Fetching from tvdatafeed...")

            df = tv.get_hist(
                symbol="XAUUSD",
                exchange="OANDA",
                interval=tf,
                n_bars=200   # 🔥 reduced for cloud speed
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

                print("✅ tvdatafeed success")
                return df

        except Exception as e:
            print("⚠️ Retry fetch:", e)
            time.sleep(2)

    print("❌ tvdatafeed failed")
    return None


# =========================
# ⏱ TIMEOUT WRAPPER (IMPORTANT)
# =========================
def fetch_data_with_timeout(interval="5m", timeout=10):

    result = {"df": None}

    def target():
        result["df"] = fetch_data(interval)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        print("⏱ Timeout reached → switching to fallback")
        return fetch_fallback_data(interval)

    return result["df"] if result["df"] is not None else fetch_fallback_data(interval)


# =========================
# 🔄 FALLBACK (YFINANCE)
# =========================
def fetch_fallback_data(interval="5m"):

    print("🔁 Using fallback (yfinance)")

    try:
        df = yf.download(
            "GC=F",  # Gold futures
            period="1d",
            interval="5m"
        )

        if df is None or df.empty:
            return None

        df.rename(columns={
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close",
            "Volume": "Volume"
        }, inplace=True)

        # ✅ Indicators
        df["ema9"] = df["Close"].ewm(span=9).mean()
        df["ema15"] = df["Close"].ewm(span=15).mean()

        print("✅ fallback success")
        return df

    except Exception as e:
        print("❌ fallback failed:", e)
        return None
import yfinance as yf
import pandas as pd

def fetch_data(symbol="GC=F", interval="5m", period="5d"):
    try:
        df = yf.download(
            symbol,
            interval=interval,
            period=period,
            progress=False
        )

        # Fix multi-index columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df is None or df.empty:
            print("❌ No data fetched")
            return None

        return df

    except Exception as e:
        print(f"❌ Data Fetch Error: {e}")
        return None
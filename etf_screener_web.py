import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.stats import rankdata

# Updated ETF List without Leverage or Short ETFs
etf_symbols = [
    "XLK", "SOXX", "IGV", "CIBR", "AIQ", "IYZ",
    "XLF", "KRE", "IAI",
    "XLV", "IBB", "IHI",
    "XLE", "XOP", "TAN",
    "XLY", "FDN",
    "XLI", "ITA",
    "XLB", "LIT",
    "XLU",
    "EFA", "VEA",
    "VWO", "EEM",
    "EWJ", "MCHI", "INDA", "EWY", "EWT", "EWZ"
]

def get_etf_data(etf_symbols, period="1y", interval="1d"):
    """Fetch historical price data for ETFs using Yahoo Finance API."""
    try:
        data = yf.download(etf_symbols, period=period, interval=interval)["Close"]
        if data.empty:
            st.error("Yahoo Finance returned empty data. Check ETF symbols and API limits.")
            st.stop()
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        st.stop()

def calculate_rs(data, lookback_periods):
    """Calculate moving averages and RS ratings."""
    ma_200 = data.rolling(window=200).mean()
    ma_50 = data.rolling(window=50).mean()
    ema_5 = data.ewm(span=5, adjust=False).mean()
    ema_20 = data.ewm(span=20, adjust=False).mean()

    above_ma_200 = data.iloc[-1] > ma_200.iloc[-1]
    above_ma_50 = data.iloc[-1] > ma_50.iloc[-1]
    ema_trend = np.where(ema_5.iloc[-1] > ema_20.iloc[-1], "EMA 5 > EMA 20", "EMA 5 < EMA 20")

    rs_ratings = {}
    for period, days in lookback_periods.items():
        valid_data = data.iloc[-days:].dropna()
        ranked = rankdata(valid_data, method="average") / len(valid_data) * 99
        rs_ratings[period] = dict(zip(valid_data.index, np.round(ranked, 2)))

    return ma_200, ma_50, ema_5, ema_20, above_ma_200, above_ma_50, ema_trend, rs_ratings

def apply_filters(etf_ranking, filters):
    """Apply filters to the ETF ranking DataFrame."""
    filtered_etf_ranking = etf_ranking.query(" & ".join([f"{col} {operator} {value}" for col, operator, value in filters.items()]))
    return filtered_etf_ranking

def main():
    st.title("ETF Screener & RS Ranking")
    st.write("Live ETF ranking based on relative strength.")

    lookback_periods = {"12M": 252, "3M": 63, "1M": 20, "1W": 5}

    data = get_etf_data(etf_symbols)
    ma_200, ma_50, ema_5, ema_20, above_ma_200, above_ma_50, ema_trend, rs_ratings = calculate_rs(data, lookback_periods)

    etf_ranking = pd.DataFrame({
        "ETF": data.columns,
        "Above 200 MA": [above_ma_200],
        "Above 50 MA": [above_ma_50],
        "EMA Trend": [ema_trend]
    })
    etf_ranking = etf_ranking.assign(**rs_ratings)

    # Add filters with better UI and improved filter application
    filters = {
        "Above 200 MA": ("==", st.sidebar.checkbox("Above 200 MA")),
        "Above 50 MA": ("==", st.sidebar.checkbox("Above 50 MA")),
        "EMA Trend": ("==", st.sidebar.selectbox("EMA Trend", ["EMA 5 > EMA 20", "EMA 5 < EMA 20", "Unknown"]))
    }

    etf_ranking = apply_filters(etf_ranking, [(k, v[0], v[1]) for k, v in filters.items() if v[1]])

    st.dataframe(etf_ranking.sort_values(by="RS Rating 12M", ascending=False))

    st.download_button(
        label="Download CSV",
        data=etf_ranking.to_csv(index=False),
        mime="text/csv",
        filename="etf_ranking.csv"
    )

if __name__ == "__main__":
    main()

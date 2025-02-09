import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.stats import rankdata

# Updated ETF symbols list without leverage or short ETFs
etf_symbols = [
    "XLK", "SOXX", "IGV", "CIBR", "AIQ", "IYZ",
    "XLF", "KRE", "IAI",
    "XLV", "IBB", "IHI",
    "XLE", "XOP", "TAN",
    "XLY", "FDN",
    "XLB", "LIT",
    "XLU",
    "EFA", "VEA",
    "VWO", "EEM",
    "EWJ", "MCHI", "INDA", "EWY", "EWT", "EWZ"
]

LOOKBACK_PERIODS = {"12M": 252, "3M": 63, "1M": 20, "1W": 5}

def get_etf_data(etf_symbols, period="1y", interval="1d"):
    """Fetch historical price data for ETFs using Yahoo Finance API."""
    try:
        data = yf.download(etf_symbols, period=period, interval=interval)
        if data.empty:
            st.error("Yahoo Finance returned empty data. Check ETF symbols and API limits.")
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")

def calculate_metrics(data):
    """Calculate moving averages and RS ratings."""
    data["MA_200"] = data["Close"].rolling(window=200).mean()
    data["MA_50"] = data["Close"].rolling(window=50).mean()

    if data.isna().any().any():
        st.error("Data contains NaN values. Please check the fetched data.")

    rs_ratings = {}
    for period, days in LOOKBACK_PERIODS.items():
        valid_data = data["Close"].iloc[-days:].dropna()
        rs_rating = (valid_data / valid_data.iloc[0] - 1) * 100
        rs_ratings[period] = rs_rating

    return data, rs_ratings

def apply_filters(etf_ranking, filters):
    """Apply filters to the ETF ranking DataFrame."""
    conditions = []
    for col, (operator, value) in filters.items():
        if value:
            if operator == ">":
                condition = etf_ranking[col] > etf_ranking["12M"]
            elif operator == "<":
                condition = etf_ranking[col] < etf_ranking["12M"]
            else:
                st.error("Invalid operator. Only '>' and '<' are supported.")
                return etf_ranking
        conditions.append(condition)
    etf_ranking = etf_ranking[conditions[0]]
    for condition in conditions[1:]:
        etf_ranking = etf_ranking[condition]
    return etf_ranking

def main():
    st.title("ETF Screener & RS Ranking")
    st.write("Live ETF ranking based on relative strength.")

    data = get_etf_data(etf_symbols)
    data, rs_ratings = calculate_metrics(data)

    data = pd.concat([data, pd.DataFrame(rs_ratings).T], axis=1)

    etf_ranking = data[["MA_200", "MA_50", "12M", "3M", "1M", "1W"]].rename(columns={
        "MA_200": "Above 200 MA",
        "MA_50": "Above 50 MA"
    })

    filters = {
        "Above 200 MA": (">", st.sidebar.checkbox("Above 200 MA")),
        "Above 50 MA": (">", st.sidebar.checkbox("Above 50 MA")),
        "EMA Trend": ("==", st.sidebar.selectbox("EMA Trend", ["EMA > EMA 20", "EMA < EMA 20", "Unknown"]))
    }

    etf_ranking = apply_filters(etf_ranking, filters)

    st.dataframe(etf_ranking.sort_values(by="12M", ascending=False))

    st.download_button(
        label="Download CSV",
        data=etf_ranking.to_csv(index=False),
        mime="text/csv",
        filename="etf_ranking.csv"
    )

if __name__ == "__main__":
    main()

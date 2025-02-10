import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# Define a function to fetch data for a single ETF
def fetch_etf_data(etf_symbol: str) -> pd.Series:
    try:
        data = yf.download(etf_symbol, period="1y", interval="1d")
        if data.empty:
            st.warning(f"No data found for {etf_symbol}")
            return None
        return data['Close']
    except Exception as e:
        st.error(f"Error fetching data for {etf_symbol}: {e}")
        return None

# Define a function to calculate the performance for a single ETF
def calculate_performance(etf_data: pd.Series, lookback_periods: dict) -> dict:
    if etf_data is None or etf_data.empty:
        return {}
    performance = {}
    for period, days in lookback_periods.items():
        if len(etf_data) >= days:
            performance[period] = round(((etf_data.iloc[-1] - etf_data.iloc[-days]) / etf_data.iloc[-days] * 100), 2)
        else:
            performance[period] = np.nan
    return performance

# Define a function to calculate the RS rating for a single ETF
def calculate_rs_rating(performance: dict) -> dict:
    if not performance:
        return {}
    rs_ratings = {}
    max_performance = max([v for v in performance.values() if not np.isnan(v)], default=1)
    for period, value in performance.items():
        if not np.isnan(value):
            rs_ratings[period] = round(value / max_performance * 99, 2)
        else:
            rs_ratings[period] = np.nan
    return rs_ratings

# Main function
def main():
    st.title("ETF Screener")

    # Define ETF symbols and lookback periods
    etf_symbols = [
        "XLK", "SOXX", "IGV", "CIBR", "XLF", "XLV", "XLE", "XLY", "GLD", "TLT"
    ]
    lookback_periods = {"12M": 252, "3M": 63, "1M": 21, "1W": 5}

    # Initialize data structures
    etf_data = {}
    performance = {}
    rs_ratings = {}

    # Fetch and process data for each ETF
    for etf_symbol in etf_symbols:
        data = fetch_etf_data(etf_symbol)
        if data is not None:
            etf_data[etf_symbol] = data
            perf = calculate_performance(data, lookback_periods)
            performance[etf_symbol] = perf
            rs_ratings[etf_symbol] = calculate_rs_rating(perf)

    # Create a DataFrame for rankings
    etf_ranking = pd.DataFrame({
        "ETF": list(etf_data.keys()),
        "RS Rating 12M": [rs_ratings[etf].get("12M", np.nan) for etf in etf_data],
        "RS Rating 3M": [rs_ratings[etf].get("3M", np.nan) for etf in etf_data],
        "RS Rating 1M": [rs_ratings[etf].get("1M", np.nan) for etf in etf_data],
        "RS Rating 1W": [rs_ratings[etf].get("1W", np.nan) for etf in etf_data],
    })

    # Add moving averages and EMA trends
    etf_ranking["Above 200 MA"] = [
        etf_data[etf].iloc[-1] > etf_data[etf].rolling(window=200).mean().iloc[-1] if len(etf_data[etf]) >= 200 else False
        for etf in etf_ranking["ETF"]
    ]
    etf_ranking["Above 50 MA"] = [
        etf_data[etf].iloc[-1] > etf_data[etf].rolling(window=50).mean().iloc[-1] if len(etf_data[etf]) >= 50 else False
        for etf in etf_ranking["ETF"]
    ]
    etf_ranking["EMA 5 > EMA 20"] = [
        etf_data[etf].ewm(span=5, adjust=False).mean().iloc[-1] > etf_data[etf].ewm(span=20, adjust=False).mean().iloc[-1]
        if len(etf_data[etf]) >= 20 else False
        for etf in etf_ranking["ETF"]
    ]

    # Sidebar filters
    st.sidebar.header("Filters")
    if st.sidebar.checkbox("RS 12M > 80"):
        etf_ranking = etf_ranking[etf_ranking["RS Rating 12M"] > 80]
    if st.sidebar.checkbox("Above 200 MA"):
        etf_ranking = etf_ranking[etf_ranking["Above 200 MA"]]
    if st.sidebar.checkbox("Above 50 MA"):
        etf_ranking = etf_ranking[etf_ranking["Above 50 MA"]]
    if st.sidebar.checkbox("EMA 5 > EMA 20"):
        etf_ranking = etf_ranking[etf_ranking["EMA 5 > EMA 20"]]

    # Display DataFrame
    st.dataframe(etf_ranking.sort_values(by="RS Rating 12M", ascending=False))

    # Download button
    st.download_button(
        label="Download CSV",
        data=etf_ranking.to_csv(index=False),
        file_name="etf_ranking.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()

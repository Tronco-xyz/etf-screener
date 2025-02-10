import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# Define a function to fetch data for a single ETF
def fetch_etf_data(etf_symbol: str) -> pd.DataFrame:
    try:
        data = yf.download(etf_symbol, period="1y", interval="1d")
        return data['Close']
    except Exception as e:
        st.error(f"Error fetching data for {etf_symbol}: {e}")
        return None

# Define a function to calculate the performance for a single ETF
def calculate_performance(etf_data: pd.DataFrame, lookback_periods: dict) -> dict:
    if etf_data is None:
        return {}
    performance = {}
    for period, days in lookback_periods.items():
        if len(etf_data) >= days:
            performance[period] = round(((etf_data.iloc[-1] - etf_data.iloc[-days]) / etf_data.iloc[-days] * 100), 2)
        else:
            performance[period] = np.nan
    return performance

# Define a function to calculate the RS rating for a single ETF
def calculate_rs_rating(performance: dict, lookback_periods: dict) -> dict:
    if not performance:
        return {}
    rs_ratings = {}
    for period in lookback_periods.keys():
        if period in performance and not np.isnan(performance[period]):
            rs_ratings[period] = round(performance[period] / max(performance.values()) * 99, 2)
        else:
            rs_ratings[period] = np.nan
    return rs_ratings

# Define the main function
def main():
    # Define the ETF symbols
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
        "EWJ", "MCHI", "INDA", "EWY", "EWT", "EWZ", 
        "GLD", "SLV", "GDX", 
        "USO", "BNO", 
        "DBC", "DBA", "LIT", 
        "TLT", "IEF", "SHY", 
        "LQD", "HYG", 
        "MUB", 
        "BNDX", "EMB"
    ]

    # Define the lookback periods
    lookback_periods = {"12M": 252, "3M": 63, "1M": 21, "1W": 5}

    # Initialize the dataframes
    etf_data = {}
    performance = {}
    rs_ratings = {}

    # Fetch data for each ETF
    for etf_symbol in etf_symbols:
        data = fetch_etf_data(etf_symbol)
        if data is not None and not data.empty:
            etf_data[etf_symbol] = data
            performance[etf_symbol] = calculate_performance(data, lookback_periods)
            rs_ratings[etf_symbol] = calculate_rs_rating(performance[etf_symbol], lookback_periods)

    # Create a dataframe for the ETF rankings
    if etf_data:
        etf_ranking = pd.DataFrame({
            "ETF": list(etf_data.keys()),
            "RS Rating 12M": [rs_ratings[etf].get("12M", np.nan) for etf in etf_data],
            "RS Rating 3M": [rs_ratings[etf].get("3M", np.nan) for etf in etf_data],
            "RS Rating 1M": [rs_ratings[etf].get("1M", np.nan) for etf in etf_data],
            "RS Rating 1W": [rs_ratings[etf].get("1W", np.nan) for etf in etf_data],
        })
    else:
        etf_ranking = pd.DataFrame({
            "ETF": [],
            "RS Rating 12M": [],
            "RS Rating 3M": [],
            "RS Rating 1M": [],
            "RS Rating 1W": [],
        })

    # Add filters
    st.sidebar.header("Filters")
    filter_rs_12m = st.sidebar.checkbox("RS 12M > 80")
    filter_above_ma_200 = st.sidebar.checkbox("Above 200 MA")
    filter_above_ma_50 = st.sidebar.checkbox("Above 50 MA")
    filter_ema_trend = st.sidebar.checkbox("EMA 5 > EMA 20")

    # Apply filters
    if filter_rs_12m:
        etf_ranking = etf_ranking[etf_ranking["RS Rating 12M"] > 80]
    if filter_above_ma_200:
        etf_ranking["Above 200 MA"] = [etf_data[etf].iloc[-1] > etf_data[etf].rolling(window=200).mean().iloc[-1] for etf in etf_ranking["ETF"]]
        etf_ranking = etf_ranking[etf_ranking["Above 200 MA"]]
    if filter_above_ma_50:
        etf_ranking["Above 50 MA"] = [etf_data[etf].iloc[-1] > etf_data[etf].rolling(window=50).mean().iloc[-1] for etf in etf_ranking["ETF"]]
        etf_ranking = etf_ranking[etf_ranking["Above 50 MA"]]
    if filter_ema_trend:
        etf_ranking["EMA 5 > EMA 20"] = [etf_data[etf].ewm(span=5, adjust=False).mean().iloc[-1] > etf_data[etf].ewm(span=20, adjust=False).mean().iloc[-1] for etf in etf_ranking["ETF"]]
        etf_ranking = etf_ranking[etf_ranking["EMA 5 > EMA 20"]]

    # Display the ETF rankings
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

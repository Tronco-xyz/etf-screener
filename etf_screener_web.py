import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.stats import rankdata

# List of non-leveraged ETF symbols
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

# Lookback periods for RS calculation
LOOKBACK_PERIODS = {"12M": 252, "3M": 63, "1M": 20, "1W": 5}

def get_etf_data(etf_symbols, period="1y", interval="1d"):
    """Fetch historical price data for ETFs."""
    try:
        data = yf.download(etf_symbols, period=period, interval=interval)
        if data.empty:
            st.error("Yahoo Finance returned empty data. Check symbols and API limits.")
            return None
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def calculate_metrics(data):
    """Calculate technical indicators and relative strength ratings."""
    if data is None:
        return None, None
    
    # Calculate Moving Averages
    data["MA_200"] = data["Close"].rolling(window=200, min_periods=1).mean()
    data["MA_50"] = data["Close"].rolling(window=50, min_periods=1).mean()
    
    # Calculate EMA (Exponential Moving Average)
    data["EMA_20"] = data["Close"].ewm(span=20, min_periods=1).mean()
    data["EMA_Trend"] = np.where(data["Close"] > data["EMA_20"], "EMA > EMA 20", "EMA < EMA 20")
    
    # Remove NaN values in relevant columns
    data = data.dropna(subset=["MA_200", "MA_50", "EMA_Trend"])
    
    # Calculate RS Ratings
    rs_ratings = {}
    for period, days in LOOKBACK_PERIODS.items():
        if len(data) >= days:
            valid_data = data["Close"].iloc[-days:]
            rs_rating = ((valid_data / valid_data.iloc[0] - 1) * 100)
            rs_ratings[period] = rs_rating
        else:
            rs_ratings[period] = pd.Series(index=data.index, dtype='float64')
    
    return data, rs_ratings

def apply_filters(etf_ranking, filters):
    """Apply specified filters to the DataFrame."""
    if etf_ranking is None or etf_ranking.empty:
        return pd.DataFrame()
    
    conditions = []
    for col, (operator, value) in filters.items():
        if not value:
            continue
        if col == "EMA Trend":
            if operator == "==":
                condition = (etf_ranking[col] == value)
        else:
            if operator == ">":
                condition = (etf_ranking[col])
            elif operator == "<":
                condition = (~etf_ranking[col])
        conditions.append(condition)
    
    if conditions:
        combined_condition = conditions[0]
        for condition in conditions[1:]:
            combined_condition &= condition
        etf_ranking = etf_ranking[combined_condition]
    
    return etf_ranking

def main():
    st.title("Enhanced ETF Screener & RS Ranking")
    st.write("Live ranking of ETFs based on relative strength and technical indicators.")
    
    data = get_etf_data(etf_symbols, period="1y")
    if data is None:
        return
    
    data, rs_ratings = calculate_metrics(data)
    if data is None or rs_ratings is None:
        return
    
    # Organize and prepare data for display
    try:
        data = pd.concat([data, pd.DataFrame(rs_ratings).T], axis=1)
        etf_ranking = data[["MA_200", "MA_50", "EMA_Trend", "12M", "3M", "1M", "1W"]]
        etf_ranking = etf_ranking.rename(columns={
            "MA_200": "Above 200 MA",
            "MA_50": "Above 50 MA"
        })
        
        # Convert boolean columns to True/False
        etf_ranking["Above 200 MA"] = etf_ranking["Above 200 MA"].fillna(False).astype(bool)
        etf_ranking["Above 50 MA"] = etf_ranking["Above 50 MA"].fillna(False).astype(bool)
        
        # Set up filters in the sidebar
        filters = {
            "Above 200 MA": (">", st.sidebar.checkbox("Show ETFs Above 200 MA")),
            "Above 50 MA": (">", st.sidebar.checkbox("Show ETFs Above 50 MA")),
            "EMA Trend": ("==", 
                         st.sidebar.selectbox("EMA Trend Filter", 
                                           ["Show All", "EMA > EMA 20", "EMA < EMA 20"]))
        }
        
        # Apply the filters
        etf_ranking = apply_filters(etf_ranking, filters)
        
        # Display results
        st.subheader("Filtered ETF Rankings")
        cols = ["Above 200 MA", "Above 50 MA", "EMA Trend", "12M", "3M", "1M", "1W"]
        etf_ranking = etf_ranking[cols]
        st.dataframe(etf_ranking.sort_values(by="12M", ascending=False), 
                    use_container_width=True, 
                    column_config={
                        "Above 200 MA": {"type": "boolean"},
                        "Above 50 MA": {"type": "boolean"}
                    })
        
        # Add download button
        csv = etf_ranking.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="etf_ranking.csv",
            mime="text/csv",
        )
        
    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

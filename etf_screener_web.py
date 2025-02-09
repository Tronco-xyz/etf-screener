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
    """Fetch historical price data for ETFs using Yahoo Finance API."""
    try:
        data = yf.download(etf_symbols, period=period, interval=interval)
        if data.empty:
            st.error("Yahoo Finance returned empty data. Check ETF symbols and API limits.")
            return None
        # Reorganize the data to have a single-level index
        data = data.swaplevel(axis=1)
        data.columns = ['_'.join(col).strip() for col in data.columns]
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def calculate_metrics(data):
    """Calculate moving averages and RS ratings."""
    if data is None or len(data) == 0:
        st.error("No data available to calculate metrics.")
        return None, None

    try:
        # Extract the 'Close' column for each ETF
        close_prices = data[['Close_' + ticker for ticker in etf_symbols]]
        
        # Convert to numeric, coerce errors to NaN
        close_prices = close_prices.apply(pd.to_numeric, errors='coerce')
        
        # Remove any rows with NaN in 'Close' prices
        close_prices = close_prices.dropna()
        
        if close_prices.empty:
            st.error("Insufficient valid 'Close' data after filtering.")
            return None, None

        # Calculate Moving Averages
        data["MA_200"] = close_prices.rolling(window=200, min_periods=1).mean()
        data["MA_50"] = close_prices.rolling(window=50, min_periods=1).mean()

        # Calculate RS Ratings
        rs_ratings = {}
        for period, days in LOOKBACK_PERIODS.items():
            if len(close_prices) >= days:
                valid_data = close_prices.iloc[-days:]
                rs_rating = ((valid_data / valid_data.iloc[0] - 1) * 100)
                rs_ratings[period] = rs_rating.mean(axis=1)  # Calculate mean across ETFs
            else:
                st.warning(f"Not enough data points for {period} RS calculation.")
                rs_ratings[period] = pd.Series(index=data.index, dtype='float64')

        return data, rs_ratings
    except Exception as e:
        st.error(f"Error in calculate_metrics: {e}")
        return None, None

def apply_filters(etf_ranking, filters):
    """Apply specified filters to the DataFrame."""
    if etf_ranking is None or etf_ranking.empty:
        st.warning("No data available for filtering.")
        return pd.DataFrame()

    # Ensure the DataFrame has the necessary columns
    required_columns = ["Above 200 MA", "Above 50 MA", "12M", "3M", "1M", "1W"]
    if not all(col in etf_ranking.columns for col in required_columns):
        st.error("Missing required columns in etf_ranking DataFrame.")
        return etf_ranking

    # Initialize an empty DataFrame to accumulate results
    filtered_data = etf_ranking.copy()

    for col, (operator, value) in filters.items():
        if value:
            try:
                if col == "EMA Trend":
                    if operator == "==":
                        filtered_data = filtered_data[filtered_data[col] == value]
                else:
                    if operator == ">":
                        condition = filtered_data[col] > etf_ranking["12M"]
                    elif operator == "<":
                        condition = filtered_data[col] < etf_ranking["12M"]
                    else:
                        condition = pd.Series(True, index=filtered_data.index)  # default to no change
                    filtered_data = filtered_data[condition]
            except Exception as e:
                st.error(f"Error applying filter for {col}: {e}")
                continue

    return filtered_data

def main():
    st.title("ETF Screener & RS Ranking")
    st.write("Live ranking of ETFs based on relative strength.")

    data = get_etf_data(etf_symbols, period="5y")
    if data is None:
        st.error("Unable to fetch ETF data. Please try again later.")
        return

    st.write("Fetched Data:")
    st.write(data.head())
    st.write("Data Types:")
    st.write(data.dtypes)

    data, rs_ratings = calculate_metrics(data)
    if data is None or rs_ratings is None:
        st.error("Error in calculating metrics. Check the provided data.")
        return

    try:
        # Ensure rs_ratings align with data index
        rs_ratings_df = pd.DataFrame(rs_ratings).T
        rs_ratings_df.index = data.index[-rs_ratings_df.shape[0]:]

        # Concatenate data and rs_ratings properly
        data = pd.concat([data, rs_ratings_df], axis=1)

        # Prepare etf_ranking DataFrame
        etf_ranking = data[[col for col in data.columns if col.startswith('MA_') or col in LOOKBACK_PERIODS]]
        etf_ranking.columns = [col.replace('Close_', '') for col in etf_ranking.columns]

        # Convert boolean columns to True/False explicitly
        for ma_col in ['MA_200', 'MA_50']:
            etf_ranking[ma_col] = (etf_ranking[ma_col].fillna(False).astype(bool))

        # Set up filters
        filters = {
            "MA_200": (">", st.sidebar.checkbox("Show ETFs Above 200 MA")),
            "MA_50": (">", st.sidebar.checkbox("Show ETFs Above 50 MA")),
            "EMA Trend": ("==", st.sidebar.selectbox("EMA Trend Filter", ["Show All", "EMA > EMA 20", "EMA < EMA 20"]))
        }

        # Apply filters
        etf_ranking = apply_filters(etf_ranking, filters)

        # Display filtered results
        if not etf_ranking.empty:
            st.subheader("Filtered ETF Rankings")
            st.dataframe(
                etf_ranking.sort_values(by="12M", ascending=False),
                use_container_width=True,
                column_config={
                    "MA_200": {"type": "boolean"},
                    "MA_50": {"type": "boolean"}
                }
            )
        else:
            st.warning("No ETFs matching the filters.")

        # Download button
        csv = etf_ranking.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data(csv),
            file_name="etf_ranking.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"An error occurred during processing: {e}")

if __name__ == "__main__":
    main()

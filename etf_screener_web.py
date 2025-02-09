import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.stats import rankdata

# ETF symbols list
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
        # Convert 'Close' column to numeric, coercing errors to NaN
        data["Close"] = pd.to_numeric(data["Close"], errors='coerce')
        # Drop rows where 'Close' is NaN
        data = data.dropna(subset=['Close'])
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
        # Calculate Moving Averages
        data["MA_200"] = data["Close"].rolling(window=200, min_periods=1).mean()
        data["MA_50"] = data["Close"].rolling(window=50, min_periods=1).mean()

        # Remove any rows with NaN values from MA calculations
        data = data.dropna(subset=["MA_200", "MA_50"])

        # Calculate RS Ratings
        rs_ratings = {}
        for period, days in LOOKBACK_PERIODS.items():
            if len(data) >= days:
                valid_data = data["Close"].iloc[-days:].dropna()
                rs_rating = (valid_data / valid_data.iloc[0] - 1) * 100
                rs_ratings[period] = rs_rating
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

    conditions = []
    for col, value in filters.items():
        if value:
            if col == "Above 200 MA":
                condition = etf_ranking[col] == True
            elif col == "Above 50 MA":
                condition = etf_ranking[col] == True
            else:
                condition = pd.Series(True, index=etf_ranking.index)
            conditions.append(condition)

    if not conditions:
        return etf_ranking

    combined_condition = conditions[0]
    for condition in conditions[1:]:
        combined_condition &= condition

    return etf_ranking[combined_condition]

def main():
    st.title("ETF Screener & RS Ranking")
    st.write("Live ranking of ETFs based on relative strength.")

    data = get_etf_data(etf_symbols, period="5y")
    if data is None:
        st.error("Unable to fetch ETF data. Please try again later.")
        return

    # Debug: Check fetched data structure and content
    if not data.empty:
        st.write("Sample of Fetched Data:")
        st.write(data.head())
        st.write("Data Types:")
        st.write(data.dtypes)
    else:
        st.warning("No data has been fetched.")

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
        etf_ranking = data[["MA_200", "MA_50", "12M", "3M", "1M", "1W"]].rename(columns={
            "MA_200": "Above 200 MA",
            "MA_50": "Above 50 MA"
        })

        # Convert boolean columns to True/False explicitly
        etf_ranking["Above 200 MA"] = (etf_ranking["Above 200 MA"].fillna(False).astype(bool))
        etf_ranking["Above 50 MA"] = (etf_ranking["Above 50 MA"].fillna(False).astype(bool))

        # Set up filters
        filters = {
            "Above 200 MA": st.sidebar.checkbox("Show ETFs Above 200 MA"),
            "Above 50 MA": st.sidebar.checkbox("Show ETFs Above 50 MA"),
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
                    "Above 200 MA": {"type": "boolean"},
                    "Above 50 MA": {"type": "boolean"}
                }
            )
        else:
            st.warning("No ETFs matching the filters.")

        # Download button
        csv = etf_ranking.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="etf_ranking.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"An error occurred during processing: {e}")

if __name__ == "__main__":
    main()

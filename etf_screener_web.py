import streamlit as st
import yfinance as yf
import pandas as pd

# Helper function to calculate moving averages
def calculate_indicators(data):
    data['200SMA'] = data['Close'].rolling(window=200).mean()
    data['30SMA'] = data['Close'].rolling(window=30).mean()
    data['10EMA'] = data['Close'].ewm(span=10, adjust=False).mean()
    data['200SMA_Rising'] = data['200SMA'].diff() > 0
    data['30SMA_Rising'] = data['30SMA'].diff() > 0
    data['10EMA_Rising'] = data['10EMA'].diff() > 0
    return data

# Helper function to rate ETFs
def rate_etf(data):
    rating = 0
    if data['Close'].iloc[-1] > data['200SMA'].iloc[-1]:
        rating += 1
    if data['Close'].iloc[-1] > data['30SMA'].iloc[-1]:
        rating += 1
    if data['Close'].iloc[-1] > data['10EMA'].iloc[-1]:
        rating += 1
    if data['200SMA_Rising'].iloc[-1]:
        rating += 1
    if data['30SMA_Rising'].iloc[-1]:
        rating += 1
    if data['10EMA_Rising'].iloc[-1]:
        rating += 1
    return rating

# Streamlit app
st.title("ETF Rating System")

# User inputs
tickers = st.text_input("Enter ETF Tickers (comma-separated):", "SPY, QQQ, VTI")
start_date = st.date_input("Start Date", value=pd.to_datetime("2022-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("2023-12-31"))

if st.button("Rate ETFs"):
    tickers = [ticker.strip() for ticker in tickers.split(",")]
    results = []

    for ticker in tickers:
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            if data.empty:
                st.warning(f"No data found for {ticker}.")
                continue
            data = calculate_indicators(data)
            rating = rate_etf(data)
            # Append a dictionary with ticker and rating
            results.append({"Ticker": ticker, "Rating": rating})
        except Exception as e:
            st.error(f"Error processing {ticker}: {e}")

    # Ensure the DataFrame creation works only if there are results
    if results:
        results_df = pd.DataFrame(results)  # Convert list of dictionaries to DataFrame
        st.write("ETF Ratings:")
        st.dataframe(results_df)
    else:
        st.warning("No valid data to display.")

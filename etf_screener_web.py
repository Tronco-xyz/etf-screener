import pandas as pd
import numpy as np
import yfinance as yf
import ta

# List of tickers (stocks and ETFs)
tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "FB", "NFLX",
    "XLK", "SOXX", "IGV", "CIBR", "AIQ", "IYZ",
    "XLF", "KRE", "IAI", "XLV", "IBB", "IHI",
    "XLE", "XOP", "TAN",
    "XLY", "FDN",
    "XLI", "ITA",
    "XLB", "LIT",
    "XLU", "EFA", "EWJ", "MCHI", "INDA", "EWY", "FDN",
    "XLB", "LIT", "XLV", "BND",
    "BND", "LIT", "XLV", "BND",
    "BND", "LIT", "XLV",
]

# Download historical price data
data = yf.download(tickers, period="1y")["Adj Close"]

# Calculate indicators
data["EMA_10"] = data.rolling(window=10).mean()
data["EMA_20"] = data.rolling(window=20).mean()
data["RSI"] = ta.momentum.RSI(data, timeperiod=14)

# Set filters
filter_ema_cross = 0.7
filter_rsi = 75
filter_rs_90 = 90

# Screening criteria
screening_criteria = pd.DataFrame({
    "EMA_10_Cross_Above_EMA_20": (data["EMA_10"] > data["EMA_20"]).astype(int),
    "RSI_Above_75": (data["RSI"] > filter_rsi).astype(int),
    "Relative_Strength": (data.pct_change() > data.pct_change().rolling(window=252).mean()).astype(int),
})

# Apply filters
filtered_tickers = screening_criteria[
    (screening_criteria["EMA_10_Cross_Above_EMA_20"] == 1) &
    (screening_criteria["RSI_Above_75"] == 1) &
    (screening_criteria["Relative_Strength"] >= filter_rs_90)
]

# Print or save the results
print(filtered_tickers)

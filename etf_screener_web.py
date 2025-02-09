import pandas as pd
import yfinance as yf
import ta

# List of tickers ( stocks or ETFs )
tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "FB", "NFLX",
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

# Fetch historical price data
data = yf.download(tickers, period="1y", interval="1d")["Close"]

# Calculate indicators
ema_10 = data.rolling(window=10).mean()
ema_20 = data.rolling(window=20).mean()
rsi = ta.momentum.RSIIndicator(data).rsi()

# Create a DataFrame for screening criteria
screening_criteria = pd.DataFrame({
    "EMA_10_Cross_Above_EMA_20": (ema_10 > ema_20).astype(int),
    "RSI_Above_75": (rsi > 75).astype(int),
    "Relative_Strength": ((data.iloc[-1] - data.iloc[-252]) / data.iloc[-252] * 100).rank(pct=True) * 100
})

# Set filters
filter_ema_cross = True
filter_rsi = True
filter_rs_90 = True

# Apply filters
filtered_tickers = screening_criteria[(screening_criteria["EMA_10_Cross_Above_EMA_20"] == filter_ema_cross) &
                                      (screening_criteria["RSI_Above_75"] == filter_rsi) &
                                      (screening_criteria["Relative_Strength"] >= filter_rs_90)["Relative_Strength"].sort_values(ascending=False)

# Print or save the results
print(filtered_tickers)

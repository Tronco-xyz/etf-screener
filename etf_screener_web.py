import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.stats import rankdata

# Updated ETF List without Leverage or Short ETFs
etf_symbols = [
    "XLK", "XLV", "XLF", "XLY", "XLP", "XLE", "XLU", "XLI", "XLB", "XLRE", "XLC",
    "SMH", "CIBR", "BOTZ", "SKYY", "FINX", "ICLN", "XOP", "IBB", "ITA", "XME", "IFRA", "ONLN",
    "SPY", "QQQ", "DIA", "IWM", "EEM", "EFA", "TLT", "HYG",
    "VXUS", "VEU", "VSS", "SCHF", "VGK", "IEV", "EZU", "FEZ", "EWG", "EWU",
    "VWO", "EEM", "FXI", "MCHI", "ASHR", "EWJ", "FLJP", "AAXJ", "VPL",
    "EWC", "FLCA", "ILF", "EWZ", "EWW", "CWI", "ACWX", "DLS", "DGT", "IQDG",
    "GLD", "SLV", "PDBC", "DBA", "WEAT", "CORN", "SOYB", "USO", "UNG", "LIT", "REMX",
    "ARKK", "ARKG", "ARKQ", "ARKF", "WCLD", "FIVG", "XITK", "VYM", "SCHD", "SDY", "DVY"
]

# Streamlit UI
st.title("ETF Screener & RS Ranking")
st.write("Live ETF ranking based on relative strength.")

# Fetch historical price data from Yahoo Finance
st.write("Fetching latest data...")
etf_data = yf.download(etf_symbols, period="1y", interval="1d")
if etf_data.empty:
    st.error("Yahoo Finance returned empty data. Check ETF symbols and API limits.")
    st.stop()

# Extract 'Close' prices
if isinstance(etf_data.columns, pd.MultiIndex):
    etf_data = etf_data['Close']

# Ensure ETFs have enough data
available_days = etf_data.count()
max_days = available_days.max()

# Adjust 12M lookback dynamically
lookback_periods = {"12M": min(252, max_days), "3M": 63, "1M": 21, "1W": 5}

valid_etfs = [etf for etf in etf_data.columns if available_days[etf] >= 63]
etf_data = etf_data[valid_etfs]

# Calculate performance over available periods
performance = {}
for period, days in lookback_periods.items():
    performance[period] = {
        etf: ((etf_data[etf].iloc[-1] - etf_data[etf].iloc[-days]) / etf_data[etf].iloc[-days] * 100)
        if available_days[etf] >= days else np.nan for etf in valid_etfs
    }

performance_df = pd.DataFrame(performance)

# Calculate moving averages
ma_200 = etf_data.rolling(window=200).mean()
ema_5 = etf_data.ewm(span=5, adjust=False).mean()
ema_20 = etf_data.ewm(span=20, adjust=False).mean()

# Determine if price is above or below 200-day MA
above_ma_200 = etf_data.iloc[-1] > ma_200.iloc[-1]
ema_trend = pd.Series(np.where(ema_5.iloc[-1] > ema_20.iloc[-1], "EMA 5 > EMA 20", "EMA 5 < EMA 20"), index=valid_etfs)

# Calculate RS Rankings (percentile-based scores from 1-99)
rs_ratings = {}
for period in lookback_periods.keys():
    valid_performance = performance_df[period].dropna()
    ranked = rankdata(valid_performance, method="average") / len(valid_performance) * 99
    rs_ratings[period] = dict(zip(valid_performance.index, ranked))

rs_ratings_df = pd.DataFrame(rs_ratings, index=performance_df.index).fillna(np.nan)

# Store results in a DataFrame
etf_ranking = pd.DataFrame({
    "ETF": performance_df.index,
    "12M Performance (%)": performance_df["12M"].tolist(),
    "3M Performance (%)": performance_df["3M"].tolist(),
    "1M Performance (%)": performance_df["1M"].tolist(),
    "1W Performance (%)": performance_df["1W"].tolist(),
    "RS Rating 12M": rs_ratings_df["12M"].tolist(),
    "RS Rating 3M": rs_ratings_df["3M"].tolist(),
    "RS Rating 1M": rs_ratings_df["1M"].tolist(),
    "RS Rating 1W": rs_ratings_df["1W"].tolist(),
    "Above 200 MA": above_ma_200.reindex(performance_df.index).fillna(False).tolist(),
    "EMA Trend": ema_trend.reindex(performance_df.index).fillna("Unknown").tolist()
})

# Display ETF Rankings in Streamlit
top_n = st.slider("Number of top ETFs to display:", 5, len(etf_ranking), 20)
st.dataframe(etf_ranking.sort_values(by="RS Rating 12M", ascending=False).head(top_n))

# Download Button
st.download_button(
    label="Download CSV",
    data=etf_ranking.to_csv(index=False),
    file_name="etf_ranking.csv",
    mime="text/csv"
)

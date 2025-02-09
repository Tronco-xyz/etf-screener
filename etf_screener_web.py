import streamlit as st
import yfinance as yf
import pandas as pd

def get_etf_data(etf_symbols, period="1y", interval="1d"):
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
        traceback.print_exc()  # Print the full traceback for debugging purposes
        time.sleep(60)  # Add a delay before retrying
        return None

def calculate_metrics(data):
    try:
        if 'Close' not in data.columns or len(data['Close']) < 200 + 50:
            st.error("Insufficient data to calculate moving averages.")
            return pd.DataFrame()
        
        # Calculate 200-day MA
        data['MA_200'] = data['Close'].rolling(window=200).mean()
        # Check if the ETF is above its 200-day moving average
        data['Above 200 MA'] = (data['Close'] > data['MA_200']).astype(int)
        
        # Calculate 50-day MA
        data['MA_50'] = data['Close'].rolling(window=50).mean()
        # Check if the ETF is above its 50-day moving average
        data['Above 50 MA'] = (data['Close'] > data['MA_50']).astype(int)
        
        return data
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        traceback.print_exc()  # Print the full traceback for debugging purposes
        return pd.DataFrame()

def apply_filters(etf_ranking, filters):
    try:
        filtered = etf_ranking.copy()
        if not filters["Above 200 MA"]:
            filtered = filtered[~filtered['Above 200 MA']]
        if not filters["Above 50 MA"]:
            filtered = filtered[~filtered['Above 50 MA']]
        
        return filtered
    except Exception as e:
        st.error(f"Error applying filters: {e}")
        traceback.print_exc()  # Print the full traceback for debugging purposes
        return etf_ranking

def calculate_rs(data):
    try:
        if 'Close' not in data.columns or len(data['Close']) < 200 + 50:
            st.error("Insufficient data to calculate RS ratings.")
            return pd.DataFrame()
        
        # Calculate RS rating based on moving averages
        rs_ratings = []
        for index, row in data.iterrows():
            if index >= 249:  # Ensure there is enough data before the current date
                ma_50_before = data.loc[index - 201:index - 171]['MA_50'].mean()
                ma_50_after = data.loc[index + 39:index]['MA_50'].mean()
                
                if row['Above 200 MA'] == 1 and row['Above 50 MA'] == 1:
                    rs_rating = (ma_50_before - ma_50_after) / ma_50_after
                    rs_ratings.append(rs_rating)
                else:
                    rs_ratings.append(None)
            else:
                rs_ratings.append(None)

        data['RS Rating'] = pd.Series(rs_ratings, index=data.index)
        return data
    except Exception as e:
        st.error(f"Error calculating RS ratings: {e}")
        traceback.print_exc()  # Print the full traceback for debugging purposes
        return pd.DataFrame()

def main():
    st.title("ETF Data Analysis")
    
    etf_symbols = ['SPY', 'QQQ']  # Example ETF symbols, replace with your desired ones
    
    data = get_etf_data(etf_symbols)
    if data is not None:
        metrics_data = calculate_metrics(data)
        rs_data = calculate_rs(metrics_data)

        if not rs_data.empty:
            st.subheader("Filtered Results")
            
            filters = {
                "Above 200 MA": True,
                "Above 50 MA": True
            }

            filtered_results = apply_filters(rs_data, filters)

            if not filtered_results.empty:
                st.write(filtered_results)
                
                # Download button for the results
                csv = filtered_results.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="filtered_etf_data.csv">Download CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
            else:
                st.error("No data meets the filter criteria.")
        else:
            st.error("Insufficient data to calculate RS ratings.")

if __name__ == "__main__":
    main()

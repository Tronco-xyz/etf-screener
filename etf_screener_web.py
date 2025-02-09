import streamlit as st
import yfinance as yf
import pandas as pd

def get_etf_data(etf_symbols, period="1y", interval="1d"):
    try:
        data = yf.download(etf_symbols, period=period, interval=interval)
        if data.empty:
            st.error("Yahoo Finance returned empty data. Check ETF symbols and API limits.")
            return None
        
        # Ensure 'Close' column exists and is not entirely NaN
        if 'Close' not in data.columns or data['Close'].isna().all():
            st.error("Invalid 'Close' data for calculations.")
            return pd.DataFrame()
        
        # Convert 'Close' column to numeric, coercing errors to NaN
        data["Close"] = pd.to_numeric(data["Close"], errors='coerce')
        
        # Drop rows where 'Close' is NaN
        data = data.dropna(subset=['Close'])
        
        if data.empty:
            st.error("No valid 'Close' data available after filtering.")
            return None
        
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
            st.error("Insufficient data to calculate RS Rating.")
            return pd.DataFrame()
        
        # Calculate the difference between close and MA_200
        diff = data['Close'] - data['MA_200']
        
        # Normalize the differences to a scale of 1 to 5
        max_diff = diff.abs().max()
        normalized_diff = (diff / max_diff) * 4 + 1
        
        # Assign RS Rating based on normalized difference
        rs_rating = pd.cut(normalized_diff, bins=[0.25, 0.75, 1], labels=['Low', 'Medium', 'High'])
        
        data['RS_Rating'] = rs_rating
        
        return data
    except Exception as e:
        st.error(f"Error calculating RS Rating: {e}")
        traceback.print_exc()  # Print the full traceback for debugging purposes
        return pd.DataFrame()

def main():
    etf_symbols = ['SPY', 'QQQ']  # Replace with your desired ETF symbols
    
    data = get_etf_data(etf_symbols)
    
    if not data.empty:
        metrics_df = calculate_metrics(data)
        
        if not metrics_df.empty:
            filtered_df = apply_filters(metrics_df, {"Above 200 MA": True, "Above 50 MA": True})
            
            if not filtered_df.empty:
                rs_rating_df = calculate_rs(filtered_df)
                
                if not rs_rating_df.empty:
                    st.write("Filtered and Rated ETF Data:")
                    st.write(rs_rating_df)
                    
                    # Download button for the results
                    csv = rs_rating_df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="filtered_etf_data.csv">Download CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
                else:
                    st.error("No data meets the filter criteria.")
            else:
                st.error("Filtered DataFrame is empty.")
        else:
            st.error("Metrics DataFrame is empty.")
    else:
        st.error("Data fetched is empty.")

if __name__ == "__main__":
    main()

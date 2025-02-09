import pandas as pd
from yfinance import download

def get_etf_data(symbols, start_date='2013-06-05'):
    """
    Download historical price data for ETFs from Yahoo Finance.
    
    Parameters:
        symbols (str list): List of ETF tickers to download.
        start_date (str): Start date string in 'YYYY-MM-DD' format. Defaults to 2013-06-05.

    Returns:
        DataFrame: Contains Date and Close prices for each symbol, with multi-index columns ('Date', 'Ticker').
    """
    data_dict = {symbol: [] for symbol in symbols}
    
    try:
        df = download(symbols, start=start_date)
        
        # Ensure the date is unique per row
        if len(df.index.get_level_values(0)) == 1:
            raise ValueError('Duplicate dates found. Please ensure no overlapping data.')
            
        return df
    
    except Exception as e:
        print(f"Error fetching {symbols}: {e}")
        return None

def calculate_performance_metrics(data, periods):
    """
    Calculate various performance metrics for the given ETF data.
    
    Parameters:
        data (DataFrame): DataFrame with Date and Close prices.
        periods (list of str): List specifying time periods to compute returns.

    Returns:
        dict: Dictionary containing different metrics ('monthly_returns', 'quarterly_returns', 
              'three_months_rolling_average', etc.).
    """
    metric_results = {'monthly_returns': None, 'quartile_returns': None,
                      'r3m_rolling_average': None, 'ytd_return': None}
    
    for period in periods:
        if period == '12M':
            monthly_data = data[['Close']].last('BQS').to_frame()
            
            # Monthly returns
            metric_results['monthly_returns'] = (monthly_data / 
                                                  monthly_data.shift(periods_dict[period])
                                                  - 1) * 100
            
        elif period == '3Q' or ('6M' in periods):
            quarterly_data = data[['Close']].last('BQS').to_frame()
            
            # Quarters returns
            if len(quarterly_data.index.get_level_values(0)) > 2:
                metric_results['quartile_returns'] = (quarterly_data / 
                                                      quarterly_data.shift(periods_dict[period])
                                                      - 1) * 100
            
    return metric_results

def compute_rs_rating(data, window='3M'):
    """
    Compute RS ratings for each ETF based on historical performance.
    
    Parameters:
        data (DataFrame): DataFrame with Close prices and their metrics.
        window (str): Window size to calculate rolling returns. Defaults to '3M'.
        
    Returns:
        Series: Computed RS rating values for each symbol.
    """
    rs_rating = pd.Series(index=data.columns.get_level_values(1))
    
    # Calculate YTD return
    ytd_return = ((data['Close'].last('BQS') - data['Close']) / 
                 data['Close']).mean()
    
    # Rolling average of 3 months returns (R3M)
    r3m_window = periods_dict.get(window, None)
    
    if not r3m_window:
        return rs_rating
    
    ytd_return.rolling(r3m_window).apply(lambda x: ((x + 1) ** (1 / len(x))) - 1,
                                           raw=False)

    # Calculate RS ratings
    sorted_data = data.sort_values('Close', ascending=False)
    
    rank = sorted_data['Close'].rank(ascending=False, method='min')
    
    rs_rating[sorted_data.columns.get_level_values(1)] = (rank / len(sorted_data)) * 100
    
    return rs_rating

def apply_filters(data, etf_rs_rating):
    """
    Apply custom filters based on user-defined criteria.
    
    Parameters:
        data (DataFrame): Data containing various metrics and ranks.
        etf_rs_rating (Series): Series of RS ratings for each symbol.

    Returns:
        DataFrame: Subsetted dataframe after applying all the filtering conditions.
    """
    # Exclusion filter
    exclusion = (~data.index.get_level_values(1).isin(etf_rs_rating.loc[etf_rs_rating >= 80].index))
    
    filtered_data = data[exclusion]
    
    return filtered_data

def sort_etfs(filtered_data, ytd_threshold=25.0):
    """
    Sort the remaining ETF candidates based on their performance metrics and RS ratings.
    
    Parameters:
        filtered_data (DataFrame): DataFrame containing various metrics after filtering.
        ytd_threshold (float): Minimum YTD Return required to qualify for sorting.

    Returns:
        pd.DataFrame: Sorted dataframe with highest overall ranking first, considering other parameters like YTD return and RS rating.
    """
    # Check if any symbol remains in the filtered data
    if len(filtered_data) == 0 or not isinstance(filtered_data, pd.DataFrame):
        raise ValueError("No ETFs left after filtering.")
    
    # Calculate YTD Return for remaining symbols
    ytd_return = ((filtered_data['Close'].last('BQS') - 
                  filtered_data['Close']) / filtered_data['Close']).mean()
    
    # Select candidates meeting YTD return threshold criteria and have at least 250 days of history
    final_selection = filtered_data[((ytd_return > ytd_threshold) & (len(filtered_data.index.get_level_values(1)) >= 250))]
    
    if len(final_selection) == 0:
        raise ValueError("No ETFs meet the YTD return threshold criteria.")
        
    # Sort based on overall rank and other parameters
    final_ranking = pd.DataFrame(index=[0], 
                                 columns=['Symbol', 'Performance Score', 'YTD Return'])
    
    for symbol in final_selection.columns.get_level_values(1):
        score = (etf_rs_rating[symbol] / 100) * len(final_selection)
        ytd_score = ((final_selection[f"Close_{symbol}"].last('BQS') - 
                    final_selection[f"Close_{symbol}"]) / 
                   final_selection[f"Close_{symbol}"]).mean()
        
        total_score = score + (ytd_score * 0.35)  # Adding YTD importance
        
        final_ranking.loc[0, symbol] = [total_score,
                                        ytd_score if 'YTD Return' in symbols else None]
    
    return final_ranking.T

# Dictionary to map time periods to their respective number of quarters/years or months
periods_dict = {
    '12M': 1,
    '3Q': 3,
    '6M': 2,
}

# List of metrics to calculate (can be adjusted based on user requirements)
metrics_to_calculate = ['monthly_returns', 'quartile_returns']

# Calculate performance metrics
data = get_data(periods=metrics_to_calculate) # Assume get_data is a placeholder function

# Compute RS ratings for each symbol
rs_rating

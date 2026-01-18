from backend.fetcher import fetch_nse_200_symbols, fetch_stock_data
from backend.analysis import calculate_cci
import pandas as pd
import time

def test_backend():
    print("Testing NSE 200 Symbol Fetching...")
    symbols = fetch_nse_200_symbols()
    print(f"Fetched {len(symbols)} symbols. First 5: {symbols[:5]}")
    
    if not symbols:
        print("Failed to fetch symbols.")
        return

    test_symbol = symbols[0] # Pick the first one, usually a major stock
    print(f"\nTesting Data Fetching for {test_symbol}...")
    df = fetch_stock_data(test_symbol, interval="15", days=5)
    
    if df.empty:
        print(f"Failed to fetch data for {test_symbol}")
    else:
        print(f"Fetched {len(df)} candles.")
        print(df.tail())
        
        print(f"\nTesting CCI Calculation for {test_symbol}...")
        df_cci = calculate_cci(df)
        if df_cci is not None and 'CCI' in df_cci.columns:
            print("CCI Calculated successfully.")
            print(df_cci[['close', 'TP', 'MD', 'CCI']].tail())
        else:
            print("CCI Calculation Failed.")

if __name__ == "__main__":
    test_backend()

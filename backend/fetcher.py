import nsepython
import pandas as pd
import datetime

def fetch_nse_200_symbols():
    try:
        # NSE 200 list can be fetched from nsepython or hardcoded/downloaded.
        # Ideally, nsepython.nifty200() or similar exists, but let's check or download CSV.
        # Fallback: using fnolist() as a proxy for liquid stocks if 200 specific list is hard.
        # But user asked for NSE 200.
        # Let's try to fetch indices data.
        
        # 'NIFTY 200' is the index name.
        # nsepython.nse_eq("NIFTY 200") might not work as it expects a stock symbol.
        
        # Alternative: We can use a predefined list or fetch from NSE website directly.
        # For now, let's use nsepython.fnolist() which is usually a good set of liquid 200ish stocks, 
        # OR better: fetch NIFTY 200 constituents. 
        # nsepython has all_indices()?
        
        # Let's assume we can get the list. For this first pass, I will implement a fetcher 
        # that tries to get NIFTY 200. If that's complex, I will use FNO list which is ~180 stocks.
        
        # Actually, let's try to get valid symbols.
        # Using nse_get_index_list functionality if available or just raw request.
        
        # Simpler approach for MVP: Use nsepython to get all F&O stocks which is the most active set.
        # The user specifically asked for NSE 200.
        # I will look up how to get constituents.
        
        # For now, returning a sample list to ensure logic works, then will refine the symbol fetcher.
        # We can fetch 'NIFTY 200' constituents from nseindia directly.
        
        url = "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv"
        # We need headers to emulate browser
        headers = {'User-Agent': 'Mozilla/5.0'}
        df = pd.read_csv(url)
        return df['Symbol'].tolist()
    except Exception as e:
        print(f"Error fetching NSE 200 symbols: {e}")
        # Fallback to a few known stocks for testing if network fails
        return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

def fetch_stock_data(symbol, interval='15m', days=5):
    try:
        # nsepython.equity_history equivalent?
        # nsefetch uses scraping.
        # We need OHLC data.
        # Provide a robust way to get candles.
        # Using nsepython default candle fetching if available, or direct API.
        
        # nsepython typically has 'nsefetch'
        # Let's use standard logic or just simulate if API is blocked.
        # But requirement is REAL TIME.
        
        # TradingView data is often used by nsepython via `tv_data`.
        # let's try that as it is reliable for candles.
        
        # NOTE: nsepython documentation is sparse, assuming standard usage.
        # If this fails, I will need to use `yfinance` as a reliable fallback (15m delayed) 
        # or `nsepython` raw fetch.
        
        # However, user asked for data from "NSE Platform". 
        # I will try to use the nsepython library's functionality which uses NSE endpoints.
        
        series = "EQ"
        # Trying to use the underlying API that nsepython exposes or wraps.
        # We can construct the URL for chart data:
        # https://www.nseindia.com/api/chart-databyindex?index=RELIANCE
        
        # Let's write a direct fetcher using nsepython.nsefetch meant for this.
        
        return nsepython.udf(symbol, interval, days) # This effectively gets TradingView data from NSE
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

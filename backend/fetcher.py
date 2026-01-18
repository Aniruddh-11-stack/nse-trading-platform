import requests
import pandas as pd
import datetime

def fetch_nse_200_symbols():
    try:
        # Fetch NIFTY 200 list from a stable source or fallback
        url = "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            df = pd.read_csv(url)
            return df['Symbol'].tolist()
        except:
             return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK", "LTI"]
    except Exception as e:
        print(f"Error fetching NSE 200 symbols: {e}")
        return ["RELIANCE", "TCS"]

def fetch_stock_data(symbol, interval='15m', days=5):
    try:
        # Yahoo Finance Chart API
        yf_symbol = f"{symbol}.NS"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}"
        params = {
            'interval': interval,
            'range': f"{days}d"
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        
        if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
            return pd.DataFrame()
            
        result = data['chart']['result'][0]
        meta = result.get('meta', {})
        timestamps = result.get('timestamp', [])
        quote = result.get('indicators', {}).get('quote', [{}])[0]
        
        if not timestamps or not quote:
            return pd.DataFrame()
            
        df = pd.DataFrame({
            'timestamp': pd.to_datetime(timestamps, unit='s'),
            'open': quote.get('open', []),
            'high': quote.get('high', []),
            'low': quote.get('low', []),
            'close': quote.get('close', []),
            'volume': quote.get('volume', [])
        })
        
        # Filter out NaN rows (sometimes happens in Yahoo data)
        df = df.dropna()
        
        return df
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

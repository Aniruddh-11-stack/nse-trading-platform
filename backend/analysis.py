import pandas as pd
# import pandas_ta as ta # Removing dependency as discussed
from .fetcher import fetch_stock_data, fetch_nse_200_symbols
import time

def calculate_cci(df, period=20):
    if df.empty:
        return None
    
    # CCI = (TP - SMA(TP)) / (0.015 * MeanDeviation(TP))
    # TP = (High + Low + Close) / 3
    
    # Ensure correct columns
    try:
        # df typically has 'close', 'high', 'low' from nsepython/udf
        # converting to float
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        
        df['TP'] = (df['high'] + df['low'] + df['close']) / 3
        df['SMA_TP'] = df['TP'].rolling(window=period).mean()
        df['MD'] = df['TP'].rolling(window=period).apply(lambda x: pd.Series(x).mad())
        # pandas MAD is deprecated in newer versions? 
        # Alternative: (x - x.mean()).abs().mean()
        
        # Let's do explicit Mean Deviation
        # rolling().apply() is slow. 
        # Optimization: Use rolling_apply from libraries or standard implementation.
        # For simplicity and speed on 15m data (small dataset per stock), apply is okay.
        
        def mean_deviation(x):
            return (x - x.mean()).abs().mean()
            
        df['MD'] = df['TP'].rolling(window=period).apply(mean_deviation, raw=True)
        
        df['CCI'] = (df['TP'] - df['SMA_TP']) / (0.015 * df['MD'])
        
        return df
    except Exception as e:
        print(f"Error calculating CCI: {e}")
        return None

def scan_stocks():
    symbols = fetch_nse_200_symbols()
    bullish_stocks = []
    
    print(f"Scanning {len(symbols)} stocks...")
    
    for symbol in symbols:
        try:
            # Getting 15m candles
            df = fetch_stock_data(symbol, "15") 
            if df.empty or len(df) < 20: # Need enough data for CCI
                continue
                
            df_cci = calculate_cci(df)
            if df_cci is None:
                continue
                
            # Check last candle or second to last (completed candle)
            # "Crosses 100" means it was below 100 and now is above 100? 
            # OR just strictly > 100 currently? 
            # "Crosses 100" typically implies a crossover event.
            # Let's check if Current CCI > 100.
            
            # To be precise on "crosses 100", we check:
            # Prev CCI < 100 AND Curr CCI > 100
            
            current_cci = df_cci['CCI'].iloc[-1]
            prev_cci = df_cci['CCI'].iloc[-2]
            
            signal_type = None
            
            # Bullish Cross: Prev <= 100, Current > 100
            if prev_cci <= 100 and current_cci > 100:
                signal_type = "BULLISH"
                
            # Bearish Cross: Prev >= -100, Current < -100
            elif prev_cci >= -100 and current_cci < -100:
                signal_type = "BEARISH"
                
            if signal_type:
                print(f"Signal found: {symbol} ({signal_type}, CCI: {current_cci:.2f})")
                bullish_stocks.append({
                    "symbol": symbol,
                    "type": signal_type,
                    "cci": current_cci,
                    "price": df_cci['close'].iloc[-1],
                    "time": datetime.datetime.now().isoformat()
                })
                
            # Initial simple check > 100 for now to catch active trends too? 
            # User said "crosses 100", usually implies fresh signal.
            
            time.sleep(0.1) # Rate limiting to be nice to NSE
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
            continue
            
    return bullish_stocks

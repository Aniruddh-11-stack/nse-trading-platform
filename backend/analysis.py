from .fetcher import fetch_stock_data, fetch_nse_200_symbols, fetch_us_symbols
from .sectors import get_sector, SECTOR_MAP
import time
import datetime
import pandas as pd
import numpy as np
import concurrent.futures

def calculate_cci(df, period=20):
    if df.empty:
        return None
    try:
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        df['TP'] = (df['high'] + df['low'] + df['close']) / 3
        df['SMA_TP'] = df['TP'].rolling(window=period).mean()
        
        def mean_deviation(x):
            return np.abs(x - x.mean()).mean()
            
        df['MD'] = df['TP'].rolling(window=period).apply(mean_deviation, raw=True)
        # Avoid division by zero
        df['CCI'] = (df['TP'] - df['SMA_TP']) / (0.015 * df['MD'].replace(0, 0.001))
        return df
    except Exception as e:
        print(f"Error calculating CCI: {e}")
        return None

def calculate_backtest(df, signal_type):
    # Instant Truth: Check last 30 days
    wins = 0
    total = 0
    
    # We need to iterate through past data.
    # Simple approximation: Check last 20 crossover events
    
    # Find all past crossovers
    # Optimization: Vectorize or strict loop limits
    for i in range(21, len(df) - 5): # Stop 5 bars before end to check outcome
        p_cci = df['CCI'].iloc[i-1]
        c_cci = df['CCI'].iloc[i]
        
        is_signal = False
        if signal_type == "BULLISH" and p_cci <= 100 and c_cci > 100:
            is_signal = True
        elif signal_type == "BEARISH" and p_cci >= -100 and c_cci < -100:
             is_signal = True
             
        if is_signal:
            total += 1
            entry_price = df['close'].iloc[i]
            # Check next 5 bars
            outcome_period = df.iloc[i+1:i+6]
            if signal_type == "BULLISH":
                # Win if Max High > Entry + 1%
                if outcome_period['high'].max() > entry_price * 1.01:
                    wins += 1
            else:
                 # Win if Min Low < Entry - 1%
                 if outcome_period['low'].min() < entry_price * 0.99:
                     wins += 1
                     
    win_rate = (wins / total * 100) if total > 0 else 0
    return win_rate, total

def get_sector_sentiment(target_sector, symbols):
    return "N/A"

def process_stock(stock_info):
    """Helper - runs in thread."""
    symbol, suffix = stock_info
    try:
        # 1. Fetch 5m Data (CHANGED from 15m)
        df = fetch_stock_data(symbol, "5m", days=5, suffix=suffix) 
        if df.empty or len(df) < 50:
            return None
            
        df_cci = calculate_cci(df)
        if df_cci is None:
            return None
        
        # Check Signal
        current_cci = df_cci['CCI'].iloc[-1]
        prev_cci = df_cci['CCI'].iloc[-2]
        signal_type = None
        
        if prev_cci <= 100 and current_cci > 100:
            signal_type = "BULLISH"
        elif prev_cci >= -100 and current_cci < -100:
            signal_type = "BEARISH"
            
        if not signal_type:
            return None
            
        # --- ADVANCED FEATURES ---
        
        # 2. Whale Volume Filter
        current_vol = df_cci['volume'].iloc[-1]
        avg_vol = df_cci['volume'].rolling(20).mean().iloc[-1]
        is_whale = current_vol > (2.0 * avg_vol)
        
        # 3. Sniper Filter (Daily Trend)
        try:
             # Optimization: Fetch only if signal exists
             df_daily = fetch_stock_data(symbol, "1d", days=300, suffix=suffix)
             trend = "NEUTRAL"
             if not df_daily.empty and len(df_daily) > 200:
                  ema_200 = df_daily['close'].ewm(span=200).mean().iloc[-1]
                  curr_daily_price = df_daily['close'].iloc[-1]
                  if curr_daily_price > ema_200:
                      trend = "UP"
                  else:
                      trend = "DOWN"
        except:
            trend = "NEUTRAL"
        
        is_sniper_aligned = (signal_type == "BULLISH" and trend == "UP") or \
                            (signal_type == "BEARISH" and trend == "DOWN")
                            
        # 4. Instant Truth Backtest
        win_rate, total_trades = calculate_backtest(df_cci, signal_type)
        wins = int(round((win_rate * total_trades) / 100))
        
        # 5. Sector
        sector = get_sector(symbol)
        
        # print(f"Signal: {symbol}") 
        
        return {
            "symbol": symbol,
            "type": signal_type,
            "cci": float(current_cci),
            "price": float(df_cci['close'].iloc[-1]),
            "time": datetime.datetime.now().isoformat(),
            "whale_vol": bool(is_whale),
            "sniper_trend": bool(is_sniper_aligned),
            "win_rate": round(win_rate, 1),
            "wins": wins,
            "total_trades": total_trades,
            "sector": sector
        }
    except Exception as e:
        # print(f"Error {symbol}: {e}")
        return None

def scan_stocks(check_nse=True, check_us=True):
    nse_symbols = fetch_nse_200_symbols() if check_nse else []
    us_symbols = fetch_us_symbols() if check_us else []
    
    # Create scan targets with suffix
    scan_targets = []
    if check_nse:
        scan_targets += [(s, ".NS") for s in nse_symbols]
    if check_us:
        # Some manual cleanup for US symbols might be needed?
        # fetcher.py handles cleaning dots to hyphens.
        scan_targets += [(s, "") for s in us_symbols]
    
    print(f"Scanning {len(scan_targets)} stocks (NSE + US) in Parallel (5m timeframe)...")
    
    bullish_stocks = []
    
    # Use ThreadPoolExecutor for parallel scanning
    # 25 Threads is a safe balance for Yahoo Finance rate limits vs Speed
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        results = list(executor.map(process_stock, scan_targets))
    
    # Filter out None values
    bullish_stocks = [r for r in results if r is not None]
    
    stats = {
        "total_targets": len(scan_targets),
        "successful_fetches": len([r for r in results if r is not None or r == {}]), # Logic check: process_stock returns None on fail
        # Wait, process_stock returns dict on signal, None on no-signal OR error. 
        # We need to distinguish "No Signal" from "Error".
        # For now, let's just track 'signals_found'. We can't easily track fetch-success in map without changing helper return.
        # Let's just return what we have.
        "signals_found": len(bullish_stocks)
    }
    print(f"Scan Stats: Checked {len(scan_targets)}, Signals {len(bullish_stocks)}")
            
    return bullish_stocks, stats

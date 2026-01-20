from .fetcher import fetch_stock_data, fetch_nse_200_symbols, fetch_us_symbols
from .sectors import get_sector, SECTOR_MAP
import time
import datetime
import pandas as pd
import numpy as np

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
        df['CCI'] = (df['TP'] - df['SMA_TP']) / (0.015 * df['MD'])
        return df
    except Exception as e:
        print(f"Error calculating CCI: {e}")
        return None

def calculate_backtest(df, signal_type):
    # Instant Truth: Check last 30 days (assuming df has enough data)
    # Win = Price moved 1% in favor within next 5 bars without hitting 1% stop loss
    wins = 0
    total = 0
    
    # We need to iterate through past data.
    # Simple approximation: Check last 20 crossover events
    # This is compute intenstive, so we limit lookback
    
    events = []
    # Find all past crossovers
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
    # Crude way: Fetch ALL sector stocks and check % change. 
    # Too slow to fetch all for every scan.
    # Optimization: Main scan loop populates a global "Last known % change" for each stock.
    # For now, return "Unknown" to keep it fast, or implement independent sector scanner.
    # MVP: Just return N/A or implement later properly.
    return "N/A"

def scan_stocks(check_nse=True, check_us=True):
    nse_symbols = fetch_nse_200_symbols() if check_nse else []
    us_symbols = fetch_us_symbols() if check_us else []
    
    # Create scan targets with suffix
    # NSE stocks get .NS, US stocks get empty suffix
    scan_targets = []
    if check_nse:
        scan_targets += [(s, ".NS") for s in nse_symbols]
    if check_us:
        scan_targets += [(s, "") for s in us_symbols]
    
    bullish_stocks = []
    
    print(f"Scanning {len(scan_targets)} stocks (NSE + US) with Advanced Filters...")
    
    for symbol, suffix in scan_targets:
        try:
            # 1. Fetch 15m Data (Backtesting + Signal)
            df = fetch_stock_data(symbol, "15m", days=10, suffix=suffix) # 10 days for backtest context
            if df.empty or len(df) < 50:
                continue
                
            df_cci = calculate_cci(df)
            if df_cci is None:
                continue
            
            # Check Signal
            current_cci = df_cci['CCI'].iloc[-1]
            prev_cci = df_cci['CCI'].iloc[-2]
            signal_type = None
            
            if prev_cci <= 100 and current_cci > 100:
                signal_type = "BULLISH"
            elif prev_cci >= -100 and current_cci < -100:
                signal_type = "BEARISH"
                
            if not signal_type:
                continue
                
            # --- ADVANCED FEATURES ---
            
            # 2. Whale Volume Filter
            # Vol > 200% of 20 SMA Vol
            current_vol = df_cci['volume'].iloc[-1]
            avg_vol = df_cci['volume'].rolling(20).mean().iloc[-1]
            is_whale = current_vol > (2.0 * avg_vol)
            
            # 3. Sniper Filter (Daily Trend)
            # Need daily data.
            # Optimization: Fetch only if 15m signal exists to save API calls
            df_daily = fetch_stock_data(symbol, "1d", days=300)
            trend = "NEUTRAL"
            if not df_daily.empty and len(df_daily) > 200:
                 ema_200 = df_daily['close'].ewm(span=200).mean().iloc[-1]
                 curr_daily_price = df_daily['close'].iloc[-1]
                 if curr_daily_price > ema_200:
                     trend = "UP"
                 else:
                     trend = "DOWN"
            
            # Filter check: Bullish signal needs Up trend, Bearish needs Down
            is_sniper_aligned = (signal_type == "BULLISH" and trend == "UP") or \
                                (signal_type == "BEARISH" and trend == "DOWN")
                                
            # 4. Instant Truth Backtest
            win_rate, total_trades = calculate_backtest(df_cci, signal_type)
            wins = int(round((win_rate * total_trades) / 100))
            
            # 5. Sector
            sector = get_sector(symbol)
            
            print(f"Signal: {symbol} ({signal_type}) | Whale: {is_whale} | Sniper: {is_sniper_aligned} | WinRate: {win_rate:.0f}%")
            
            bullish_stocks.append({
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
            })
            
            time.sleep(0.1) 
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
            continue
            
    return bullish_stocks

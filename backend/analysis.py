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
        # prev_cci = df_cci['CCI'].iloc[-2] # No longer needed for strict crossover
        signal_type = None
        
        # User Request: Show ALL stocks currently above/below threshold, not just new crossovers.
        if current_cci > 100:
            signal_type = "BULLISH" # Keeping name compatible with frontend
        elif current_cci < -100:
            signal_type = "BEARISH"
        else:
            signal_type = None
            
        # --- ADVANCED FEATURES ---
        
        # 2. Whale Volume Filter
        current_vol = df_cci['volume'].iloc[-1]
        avg_vol = df_cci['volume'].rolling(20).mean().iloc[-1]
        is_whale = current_vol > (2.0 * avg_vol)
        
        # 3. Sniper Filter (Daily Trend)
        try:
             # Optimization: Fetch only if signal exists or for stats? 
             # For speed, let's only do deep trend check if we have a signal OR if we really need it.
             # Actually, for market breadth we just need CCI.
             trend = "NEUTRAL"
             if signal_type: # Only fetch daily for signals to save time/quota
                 df_daily = fetch_stock_data(symbol, "1d", days=300, suffix=suffix)
                 if not df_daily.empty and len(df_daily) > 200:
                      ema_200 = df_daily['close'].ewm(span=200).mean().iloc[-1]
                      curr_daily_price = df_daily['close'].iloc[-1]
                      if curr_daily_price > ema_200:
                          trend = "UP"
                      else:
                          trend = "DOWN"
        except:
            trend = "NEUTRAL"
        
        is_sniper_aligned = False
        if signal_type:
            is_sniper_aligned = (signal_type == "BULLISH" and trend == "UP") or \
                                (signal_type == "BEARISH" and trend == "DOWN")
                            
        # 4. Instant Truth Backtest
        win_rate = 0.0
        wins = 0
        total_trades = 0
        if signal_type:
             win_rate, total_trades = calculate_backtest(df_cci, signal_type)
             wins = int(round((win_rate * total_trades) / 100))
        
        # 5. Sector
        sector = get_sector(symbol)
        
        return {
            "symbol": symbol,
            "type": signal_type, # Can be None
            "cci": float(current_cci),
            "price": float(df_cci['close'].iloc[-1]),
            "time": datetime.datetime.now().isoformat(),
            "whale_vol": bool(is_whale),
            "sniper_trend": bool(is_sniper_aligned),
            "win_rate": round(win_rate, 1),
            "wins": wins,
            "total_trades": total_trades,
            "sector": sector,
            "is_market_bullish": float(current_cci) > 0 # Simple stat for breadth
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
    # Reduced to 10 threads as per user suggestion/Yahoo limits to avoid 429 Errors
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_stock, scan_targets))
    
    # Filter out None values
    all_results = [r for r in results if r is not None]
    
    # 1. Calculate Market Breadth
    total_analyzed = len(all_results)
    green_zone = len([r for r in all_results if r['is_market_bullish']])
    sentiment_percent = (green_zone / total_analyzed * 100) if total_analyzed > 0 else 0
    
    # Determine Market Name
    market_name = "NIFTY 200" # Default
    if check_us and not check_nse:
        market_name = "S&P 500"
    elif check_nse and not check_us:
        market_name = "NIFTY 500" # As requested
    elif check_us and check_nse:
         # Mixed mode - maybe see who has more signals or just say Global?
         # User said: "when USA Market is on we need S&P and when indian market we need Nifty"
         # We can check which list contributed more to 'all_results' or just check flags
         # Simple heuristic: If US is checked (and presumably open/active), prioritize it if NSE is closed?
         # But scan_stocks is called with flags. 
         # Let's assume the flags passed to scan_stocks reflect the "active" intent.
         # If both are True (rare in production maybe?), we can check timestamps or just list both.
         market_name = "GLOBAL MARKETS"
         
    # 2. Sector Stats
    sector_stats = {}
    for r in all_results:
        # Count only if it has a SIGNAL (active setup)
        if r['type']: 
            sec = r['sector']
            # FILTER: Exclude "Others" and "N/A"
            if sec and sec not in ["Others", "N/A"]:
                if sec not in sector_stats:
                    sector_stats[sec] = {"count": 0, "bullish": 0, "bearish": 0, "signals": []}
                
                sector_stats[sec]["count"] += 1
                if r['type'] == 'BULLISH':
                    sector_stats[sec]["bullish"] += 1
                else:
                    sector_stats[sec]["bearish"] += 1
                
                # Add symbol with direction for frontend tooltip/display
                direction_icon = "🟢" if r['type'] == 'BULLISH' else "🔴"
                sector_stats[sec]["signals"].append(f"{r['symbol']} {direction_icon}")

    # Sort sectors by signal count
    sorted_sectors = sorted(sector_stats.items(), key=lambda item: item[1]['count'], reverse=True)[:3]
    
    # Structure for Frontend
    top_sectors = []
    for name, stats in sorted_sectors:
        top_sectors.append({
            "name": name,
            "count": stats["count"],
            "bullish": stats["bullish"],
            "bearish": stats["bearish"],
            "signals": stats["signals"][:5] # Limit to top 5 symbols to avoid clutter
        })
        
    top_sector_names = [s[0] for s in sorted_sectors]

    # Filter signals for the main list
    bullish_stocks = []
    for r in all_results:
        if r['type'] is not None:
             # Calculate Confidence Score (0-100)
             score = 0
             # 1. Trend (Sniper) - 20 pts
             if r['sniper_trend']:
                 score += 20
             # 2. Volume (Whale) - 20 pts
             if r['whale_vol']:
                 score += 20
             # 3. History (Win Rate) - 20 pts
             if r['win_rate'] > 60:
                 score += 20
             # 4. Sector Resonance - 20 pts (if in top 3)
             if r['sector'] in top_sector_names:
                 score += 20
             # 5. Market Alignment - 20 pts
             # Bullish Signal + Market > 50% Bullish OR Bearish Signal + Market < 50% Bullish
             if (r['type'] == 'BULLISH' and sentiment_percent > 50) or \
                (r['type'] == 'BEARISH' and sentiment_percent < 50):
                 score += 20
                 
             r['confidence'] = score
             bullish_stocks.append(r)
    
    stats = {
        "total_targets": len(scan_targets),
        "successful_fetches": total_analyzed,
        "signals_found": len(bullish_stocks),
        "sentiment_percent": round(sentiment_percent, 1),
        "top_sectors": top_sectors,
        "market_name": market_name
    }
    print(f"Scan Stats: Checked {len(scan_targets)}, Signals {len(bullish_stocks)}")
            
    return bullish_stocks, stats

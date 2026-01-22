from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .analysis import scan_stocks
import os
from typing import List
from dotenv import load_dotenv, find_dotenv
import datetime
import pytz
from .ai_analyst import generate_stock_analysis

load_dotenv(find_dotenv())

app = FastAPI()

# Global store for latest signals
latest_signals = []


def is_market_open():
    """Check if EITHER NSE or US market is open."""
    # 1. Check NSE (IST)
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.datetime.now(ist)
    is_nse_open = False
    
    if now_ist.weekday() <= 4: # Mon-Fri
        market_open = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)
        is_nse_open = market_open <= now_ist <= market_close
        
    # 2. Check US (EST/EDT)
    est = pytz.timezone('US/Eastern')
    now_est = datetime.datetime.now(est)
    is_us_open = False
    
    if now_est.weekday() <= 4: # Mon-Fri
        # US Market: 9:30 AM - 4:00 PM ET
        market_open_us = now_est.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close_us = now_est.replace(hour=16, minute=0, second=0, microsecond=0)
        is_us_open = market_open_us <= now_est <= market_close_us

    return is_nse_open, is_us_open


def run_scan():
    """Run the scan logic - called on demand by frontend"""
    print("Starting on-demand scan...")
    
    nse_open, us_open = is_market_open()
    
    # Check if ANY market is open
    if not nse_open and not us_open:
        print("Both Markets are closed. Skipping scan.")
        return {"status": "Markets Closed"}
    
    print(f"Markets Status - NSE: {'OPEN' if nse_open else 'CLOSED'} | US: {'OPEN' if us_open else 'CLOSED'}")
    global latest_signals
    
    # Clear signals at the start of the day logic
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(ist)
    
    if latest_signals:
        try:
            first_signal_time = datetime.datetime.fromisoformat(latest_signals[0]['time'])
            if first_signal_time.tzinfo is None:
                first_signal_time = ist.localize(first_signal_time)
            
            if (now - first_signal_time).total_seconds() > 43200: 
                 print("Clearing old signals...")
                 latest_signals = []
        except Exception as e:
            print(f"Error checking signal time: {e}")

    # Filter markets based on opening hours
    new_signals, stats = scan_stocks(check_nse=nse_open, check_us=us_open)
    
    if new_signals:
        # Deduplication Logic:
        # Combine new and old, preferring new.
        # We process new_signals first, then latest_signals.
        # If a symbol is seen, skip subsequent occurrences.
        
        combined = new_signals + latest_signals
        unique_map = {}
        deduplicated_list = []
        
        for s in combined:
            if s['symbol'] not in unique_map:
                unique_map[s['symbol']] = True
                deduplicated_list.append(s)
        
        latest_signals = deduplicated_list
        print(f"Found {len(new_signals)} signals. Total unique: {len(latest_signals)}")
    else:
        print("No new signals found.")
        
    return {"status": "Scan Complete", "stats": stats, "new_signals": len(new_signals), "market_status": {"nse": nse_open, "us": us_open}}


@app.get("/api/scan")
def trigger_scan():
    """Endpoint triggered by Frontend every minute to keep app alive and scanning"""
    return run_scan()

@app.get("/api/signals")
def get_signals():
    return latest_signals

@app.get("/api/status")
def get_status():
    return {"status": "running", "mode": "on-demand"}

from pydantic import BaseModel

class Signal(BaseModel):
    symbol: str
    type: str 
    cci: float
    price: float
    time: str
    whale_vol: bool = False
    sniper_trend: bool = False
    win_rate: float = 0.0
    wins: int = 0
    total_trades: int = 0
    sector: str = "N/A"

@app.post("/api/test/inject")
def inject_signal(signal: Signal):
    global latest_signals
    latest_signals.insert(0, signal.dict())
    return {"message": "Signal injected", "current_count": len(latest_signals)}

class AnalysisRequest(BaseModel):
    type: str = "stock" # stock, definition, market, sector
    payload: dict

@app.post("/api/analyze")
def analyze_request(request: AnalysisRequest):
    """
    On-demand AI Analysis for Stocks, Definitions, Markets, or Sectors.
    """
    from .ai_analyst import analyze_data
    analysis_text = analyze_data(request.type, request.payload)
    return {"analysis": analysis_text}

@app.get("/")
def read_root():
    return FileResponse('frontend/index.html')


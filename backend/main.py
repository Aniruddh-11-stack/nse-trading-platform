from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import schedule
import time
import threading
from .analysis import scan_stocks
from .mailer import send_email
import os
from typing import List
from dotenv import load_dotenv
import datetime
import pytz

load_dotenv()

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


def job():
    print("Starting scheduled scan...")
    
    nse_open, us_open = is_market_open()
    
    # Check if ANY market is open
    if not nse_open and not us_open:
        print("Both Markets are closed. Skipping scan.")
        return
    
    print(f"Markets Status - NSE: {'OPEN' if nse_open else 'CLOSED'} | US: {'OPEN' if us_open else 'CLOSED'}")
    print("Proceeding with scan...")
    global latest_signals
    
    # Clear signals at the start of the day (approximate check)
    # If the list has signals from a previous day, clear them
    # A simple way is to check the date of the first signal
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(ist)
    today_str = now.strftime("%Y-%m-%d")
    
    if latest_signals:
        first_signal_time = datetime.datetime.fromisoformat(latest_signals[0]['time'])
        # Simple reset logic: if signal is old (> 12 hours), clear it
        # This handles both markets somewhat loosely but effectively for a persistent server
        if (now - first_signal_time).total_seconds() > 43200: 
             print("Clearing old signals...")
             latest_signals = []

    # Pass the market status to scan_stocks
    new_signals = scan_stocks(check_nse=nse_open, check_us=us_open)
    
    if new_signals:
        # Deduplicate and Append
        # we key by symbol and type and approx time? 
        # Actually, scan_stocks checks for immediate crossover. 
        # So multiple 5-min scans might not pick up the SAME crossover unless it flickers.
        # But we simply append `new_signals` to `latest_signals`
        
        # To avoid duplicates in the same 15m candle might be tricky without unique ID.
        # But let's assume `scan_stocks` logic (prev <= 100, curr > 100) is robust enough 
        # that it only fires ONCE per crossing event.
        
        # We just insert them at the beginning for display
        latest_signals = new_signals + latest_signals
        
        # Prepare email
        subject = f"NSE Update: {len(new_signals)} Stocks Crossed CCI 100"
        body = "The following stocks have crossed 100 CCI on the 15m timeframe:\n\n"
        for s in new_signals:
            whale_tag = " [WHALE 🐳]" if s.get('whale_vol') else ""
            sniper_tag = " [SNIPER 🎯]" if s.get('sniper_trend') else ""
            body += f"{s['symbol']} ({s.get('sector', 'N/A')}): {s['type']} @ {s['price']}\n"
            body += f"CCI: {s['cci']:.2f} | Win Rate: {s.get('win_rate', 0)}%{whale_tag}{sniper_tag}\n\n"
            
        # Strict check before sending email
        nse_open_now, us_open_now = is_market_open()
        if nse_open_now or us_open_now:
            recipient = os.getenv("ALERT_EMAIL")
            if recipient:
                send_email(subject, body, [recipient])
            else:
                print("No ALERT_EMAIL set.")
        else:
            print("Market closed during scan. Skipping email alert.")
    else:
        print("No new signals found this run.")

@app.on_event("startup")
def startup_event():
    # Only run the background scheduler if NOT on Vercel (local mode)
    if not os.getenv("VERCEL"):
        def run_scheduler():
            # Run once immediately
            job()
            # Then schedule
            schedule.every(5).minutes.do(job)
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        t = threading.Thread(target=run_scheduler, daemon=True)
        t.start()

@app.get("/api/cron")
def trigger_scan():
    """Endpoint for Vercel Cron to trigger the scan"""
    job()
    return {"status": "Scan triggered"}

@app.get("/api/signals")
def get_signals():
    return latest_signals

@app.get("/api/status")
def get_status():
    return {"status": "running", "scheduler": "active"}

from pydantic import BaseModel

class Signal(BaseModel):
    symbol: str
    type: str # BULLISH or BEARISH
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
    # Prepend to list
    latest_signals.insert(0, signal.dict())
    return {"message": "Signal injected", "current_count": len(latest_signals)}

@app.get("/")
def read_root():
    return FileResponse('frontend/index.html')


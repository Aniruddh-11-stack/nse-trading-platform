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


def is_market_hours():
    """Check if current time is within NSE trading hours (9:15 AM - 3:30 PM IST, Mon-Fri)"""
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(ist)
    
    # Check if it's a weekday (Monday = 0, Sunday = 6)
    if now.weekday() > 4:  # Saturday or Sunday
        return False
    
    # Market hours: 9:15 AM to 3:30 PM IST
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_open <= now <= market_close


def job():
    print("Starting scheduled scan...")
    
    # Check if market is open
    if not is_market_hours():
        print("Market is closed. Skipping scan.")
        return
    
    print("Market is open. Proceeding with scan...")
    global latest_signals
    
    # Clear signals at the start of the day (approximate check)
    # If the list has signals from a previous day, clear them
    # A simple way is to check the date of the first signal
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(ist)
    today_str = now.strftime("%Y-%m-%d")
    
    if latest_signals:
        first_signal_time = datetime.datetime.fromisoformat(latest_signals[0]['time'])
        if first_signal_time.date() < now.date():
            print("Clearing signals from previous day...")
            latest_signals = []

    new_signals = scan_stocks()
    
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
        if is_market_hours():
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


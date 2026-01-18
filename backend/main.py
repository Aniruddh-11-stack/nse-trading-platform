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

load_dotenv()

app = FastAPI()

# Global store for latest signals
latest_signals = []


def job():
    print("Starting scheduled scan...")
    global latest_signals
    signals = scan_stocks()
    latest_signals = signals
    
    if signals:
        # Prepare email
        subject = f"NSE Update: {len(signals)} Stocks Crossed CCI 100"
        body = "The following stocks have crossed 100 CCI on the 15m timeframe:\n\n"
        for s in signals:
            whale_tag = " [WHALE 🐳]" if s.get('whale_vol') else ""
            sniper_tag = " [SNIPER 🎯]" if s.get('sniper_trend') else ""
            body += f"{s['symbol']} ({s.get('sector', 'N/A')}): {s['type']} @ {s['price']}\n"
            body += f"CCI: {s['cci']:.2f} | Win Rate: {s.get('win_rate', 0)}%{whale_tag}{sniper_tag}\n\n"
            
        # Send email
        recipient = os.getenv("ALERT_EMAIL")
        if recipient:
            send_email(subject, body, [recipient])
        else:
            print("No ALERT_EMAIL set.")
    else:
        print("No signals found this run.")

@app.on_event("startup")
def startup_event():
    # Start scheduler in a separate thread
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


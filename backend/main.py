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
            body += f"{s['symbol']}: Price {s['price']}, CCI {s['cci']:.2f}\n"
            
        # Send email
        recipient = os.getenv("ALERT_EMAIL")
        if recipient:
            send_email(subject, body, [recipient])
        else:
            print("No ALERT_EMAIL set.")
    else:
        print("No signals found this run.")

def run_scheduler():
    schedule.every(5).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.on_event("startup")
def startup_event():
    # Start scheduler in a separate thread
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()

@app.get("/api/signals")
def get_signals():
    return latest_signals

@app.get("/api/status")
def get_status():
    return {"status": "running", "scheduler": "active"}

@app.get("/")
def read_root():
    return FileResponse('frontend/index.html')


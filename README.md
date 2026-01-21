# NSE 200 Trading Scanner & Algorithmic Platform 📈

A high-performance web application that scans NSE 200 (and S&P 500) stocks in real-time for CCI (Commodity Channel Index) crossovers. It identifies Bullish (>100) and Bearish (<-100) signals on a 5-minute timeframe and provides advanced institutional-grade filters.

![Dashboard Screenshot](frontend/dashboard_preview.png)

## 🚀 Key Features

### 🧠 Intelligent Decision Engine
We answer the question: *"Is this trade guaranteed?"*
-   **Trade Confidence Score (0-100%)**: Aggregates 5 distinct "Truths" (Trend, Volume, History, Sector, Market) into a single probability score.
-   **Market Sentinel**: Automatically detects if you are scanning US or Indian markets and adjusts the **Sentiment Meter** (Bullish/Bearish %) accordingly.
-   **Sector Hotspots**: Identifies which sectors are heating up (e.g., "IT is actively buying"), filtering out noise.

### Core Logic
-   **Real-time Monitoring**: Scans 200+ stocks every 5 minutes.
-   **CCI Strategy**: Triggers alerts when CCI crosses +100 (Buy) or -100 (Sell).
-   **Email Alerts**: Instant email notifications with detailed signal analysis.

### Advanced "Hedge Fund" Filters
1.  **WHALE 🐳 Filter (Smart Money)**
    *   Detects if the signal candle has **Volume > 200%** of the 20-period average.
2.  **SNIPER 🎯 Filter (Trend Alignment)**
    *   Checks the **Daily Chart** trend before alerting. Only buys if Price > 200 EMA.
3.  **INSTANT TRUTH (Backtesting)**
    *   Calculates the **Win Rate** of this specific signal for this stock over the last 30 days.

## 🛠️ Tech Stack
-   **Backend**: Python (FastAPI)
-   **Data Fetching**: Direct Yahoo Finance API (Robust & Free)
-   **Frontend**: React.js (CDN-based, No-Build) + TailwindCSS
-   **Database**: In-memory (Pandas DataFrame) for speed
-   **Deployment**: Ready for Vercel / Render / Railway

## ⚙️ Installation & Local Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Aniruddh-11-stack/nse-trading-platform.git
    cd nse-trading-platform
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the App**
    ```bash
    uvicorn backend.main:app --reload
    ```
    Access the dashboard at `http://localhost:8000`.

## 🤝 Contributing
Built by **Aniruddh-11-stack**. Feel free to fork and submit PRs!

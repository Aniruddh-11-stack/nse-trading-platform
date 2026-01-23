# NSE 200 & S&P 500 AI-Powered Trading Scanner 🚀

A high-performance algorithm that scans **NSE 200 (India)** and **S&P 500 (USA)** stocks in real-time for CCI crossovers. It combines technical indicators with **Generative AI** to provide a "Hedge Fund Manager" level analysis of every trade signal.

![Dashboard Preview](frontend/dashboard_preview.png)

## 🧠 New: AI Analyst Integration
We have integrated **OpenAI (GPT-4o)** to act as your personal cynical hedge fund manager.
-   **Signal Analysis**: Click "Analyze" on any stock to get a 3-point verdict (Buy/Short/Pass), specifically referencing price action and CCI.
-   **Market Sentiment**: A "State of the Union" address for the overall market (Bullish/Bearish).
-   **Educational Mode**: Click on terms like "Whale Volume" to get a cynical, pro-trader definition.

## ⚡ Key Features

### 1. The "Confidence" Engine
We don't just give signals; we rank them. Every stock gets a **Confidence Score (0-100%)** based on:
*   **Whale Volume** 🐳: Is institutional money moving the stock? (>200% vol).
*   **Sniper Trend** 🎯: Is the signal aligned with the daily timeframe? (200 EMA).
*   **Instant Truth**: What is the historical win rate of this signal for this specific stock?
*   **Momentum Bonus**: Extra points for strong daily price changes.

### 2. Multi-Market Support
*   **Smart Detection**: The system automatically detects if you are scanning Indian (NSE) or US stocks.
*   **Dynamic UI**: The interface adapts (Nifty 200 vs S&P 500) based on your selection.

### 3. Advanced Ranking
Stocks are sorted not just by alphabet, but by **Opportunity**.
*   **Top Rank**: High Confidence + Strong Momentum.
*   **Visual cues**: Green/Red badges for Price Change %.

## 🛠️ Tech Stack
*   **Backend**: Python (FastAPI)
*   **AI Engine**: OpenAI API (GPT-4o Mini)
*   **Frontend**: React.js (CDN, No-Build) + TailwindCSS
*   **Data**: Yahoo Finance API (`yfinance`)
*   **Deployment**: Vercel Serverless

## 🚀 Installation & Local Setup

### Prerequisites
*   Python 3.9+
*   OpenAI API Key

### 1. Clone the Repo
```bash
git clone https://github.com/Aniruddh-11-stack/nse-trading-platform.git
cd nse-trading-platform
```

### 2. Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY=sk-proj-your-key-here...
```

### 5. Run the App
```bash
uvicorn backend.main:app --reload
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

## ☁️ Deployment on Vercel

This project is optimized for Vercel Serverless deployment.

1.  **Push to GitHub**: Make sure your repo is up to date.
2.  **Import to Vercel**: Select the repository in Vercel.
3.  **Configure Project**:
    *   **Framework Preset**: Other
    *   **Build Command**: `pip install -r requirements.txt` (or leave default if using `vercel.json` config)
    *   **Output Directory**: `.` (Root)
4.  **Environment Variables** (CRITICAL):
    *   Add `OPENAI_API_KEY` in the Vercel Project Settings -> Environment Variables.
5.  **Deploy**: Click Deploy.

## 🤝 Contributing
Built by **Aniruddh-11-stack**.

> **Disclaimer**: This tool is for educational purposes only. Trading stocks involves risk.

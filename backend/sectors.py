# Hardcoded sample sector map for major NSE stocks
SECTOR_MAP = {
    "RELIANCE": "Energy", "TCS": "IT", "INFY": "IT", "HDFCBANK": "Bank", 
    "ICICIBANK": "Bank", "SBIN": "Bank", "BHARTIARTL": "Telecom", "ITC": "FMCG",
    "KOTAKBANK": "Bank", "LTI": "IT", "LT": "Infrastructure", "AXISBANK": "Bank",
    "HCLTECH": "IT", "BAJFINANCE": "Finance", "ASIANPAINT": "Consumer", 
    "MARUTI": "Auto", "TITAN": "Consumer", "ULTRACEMCO": "Cement", 
    "SUNPHARMA": "Pharma", "WIPRO": "IT", "TATAMOTORS": "Auto",
    "ADANIENT": "Metals", "ADANIPORTS": "Infrastructure", "POWERGRID": "Power",
    "NTPC": "Power", "JSWSTEEL": "Metals", "TATASTEEL": "Metals",
    "HINDUNILVR": "FMCG", "NESTLEIND": "FMCG", "ONGC": "Energy", "COALINDIA": "Energy",
    "TECHM": "IT", "HINDALCO": "Metals", "GRASIM": "Cement", "HEROMOTOCO": "Auto",
    "BAJAJ-AUTO": "Auto", "EICHERMOT": "Auto", "DRREDDY": "Pharma", "CIPLA": "Pharma",
    "DIVISLAB": "Pharma", "APOLLOHOSP": "Pharma", "BRITANNIA": "FMCG", 
    "TATACONSUM": "FMCG", "UPL": "Chemicals", "BPCL": "Energy", "SBILIFE": "Insurance",
    "HDFCLIFE": "Insurance"
}

def get_sector(symbol):
    return SECTOR_MAP.get(symbol, "Others")

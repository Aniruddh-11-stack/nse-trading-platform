import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Configure OpenAI
api_key = os.getenv("OPENAI_API_KEY")
client = None

if api_key:
    client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = "You are a cynical, high-performance hedge fund manager. Your analysis is data-driven, specific, and devoid of fluff."

def get_openai_response(prompt, max_tokens=300):
    if not client:
        return "Error: OPENAI_API_KEY not found in environment."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Service Unavailable: {str(e)}"

def generate_stock_analysis(symbol, data):
    prompt = f"""
    Analyze this stock signal for {symbol}.
    
    HARD DATA:
    - Price: ₹{data.get('price')}
    - CCI: {data.get('cci')}
    - Direction: {data.get('type')}
    - Whale Volume: {'YES' if data.get('whale_vol') else 'NO'}
    - Trend Aligned: {'YES' if data.get('sniper_trend') else 'NO'}
    - Win Rate: {data.get('win_rate', 0)}%
    
    TASK:
    Provide a cynical 3-point analysis:
    1. **Verdict**: (BUY/SHORT/PASS)
    2. **Why**: specific reference to CCI {data.get('cci')} and Price.
    3. **Risk**: based on alignment.
    
    Keep it under 100 words.
    """
    return get_openai_response(prompt)

def generate_definition(term):
    prompt = f"""
    Define "{term}" for a junior trader.
    
    CONTEXT:
    - Whale Volume: high relative trading volume indicating institutional activity.
    - Sniper Trend: signal aligns with higher timeframe trend.
    - Win Rate: historical probability of profit for this signal.
    
    TASK:
    Explain "{term}" in 1 sentence. Then give 1 cynical "Pro Tip" on how to use it.
    """
    return get_openai_response(prompt, max_tokens=150)

def generate_market_analysis(stats):
    prompt = f"""
    Analyze the overall market sentiment.
    
    DATA:
    - Bullish Stocks: {stats.get('sentiment_percent', 50)}%
    - Top Sectors: {', '.join([s['name'] for s in stats.get('top_sectors', [])])}
    
    TASK:
    Give a 'State of the Union' address for the market.
    1. **Market Gauge**: Bullish/Bearish/Choppy?
    2. **Sector Rotation**: Where is the money flowing?
    3. **Strategy**: What should I trade?
    """
    return get_openai_response(prompt)

def generate_sector_analysis(sector_name, count):
    prompt = f"""
    Analyze the {sector_name} sector.
    
    DATA:
    - Active Signals: {count}
    
    TASK:
    Is this sector heating up or cooling down? Give a quick take on whether to focus here.
    """
    return get_openai_response(prompt, max_tokens=150)

def analyze_data(type, payload):
    """
    Central dispatcher for AI analysis.
    """
    if type == 'stock':
        return generate_stock_analysis(payload.get('symbol'), payload.get('data'))
    elif type == 'definition':
        return generate_definition(payload.get('term'))
    elif type == 'market':
        return generate_market_analysis(payload.get('stats'))
    elif type == 'sector':
        return generate_sector_analysis(payload.get('name'), payload.get('count'))
    else:
        return "Invalid analysis type."

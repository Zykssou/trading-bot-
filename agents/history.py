import requests
from config import COINGECKO_API_URL

def fetch_prices(coin_id, days=30):
    try:
        url = f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart"
        r = requests.get(url, params={"vs_currency": "usd", "days": days}, timeout=10)
        if r.status_code == 200:
            return [p[1] for p in r.json().get("prices", [])]
    except Exception as e:
        print(f"[History] Erreur {coin_id}: {e}")
    return []

def ma(prices, period):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    changes = [prices[i] - prices[i-1] for i in range(-period, 0)]
    gains = [c for c in changes if c > 0]
    losses = [abs(c) for c in changes if c < 0]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def macd(prices):
    if len(prices) < 26:
        return None
    def ema(p, n):
        k = 2 / (n + 1)
        e = p[0]
        for v in p[1:]:
            e = v * k + e * (1 - k)
        return e
    ema12 = ema(prices[-12:], 12)
    ema26 = ema(prices[-26:], 26)
    return ema12 - ema26

def analyze_history(coin_id):
    prices = fetch_prices(coin_id, days=30)
    if len(prices) < 30:
        return None
    ma7 = ma(prices, 7)
    ma30 = ma(prices, 30)
    return {
        "coin": coin_id,
        "ma7": ma7,
        "ma30": ma30,
        "rsi": rsi(prices),
        "macd": macd(prices),
        "trend": "haussier" if ma7 and ma30 and ma7 > ma30 else "baissier"
    }

import requests
from config import COINGECKO_API_URL

def fetch_prices(coin_id, days=90):
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

def support_resistance(prices):
    if len(prices) < 30:
        return None, None
    recent = prices[-30:]
    support = min(recent)
    resistance = max(recent)
    return support, resistance

def volatility(prices, period=30):
    if len(prices) < period:
        return None
    recent = prices[-period:]
    avg = sum(recent) / period
    variance = sum((p - avg) ** 2 for p in recent) / period
    return (variance ** 0.5) / avg * 100

def analyze_history(coin_id):
    prices = fetch_prices(coin_id, days=90)
    if len(prices) < 30:
        return None

    ma7 = ma(prices, 7)
    ma30 = ma(prices, 30)
    ma90 = ma(prices, min(90, len(prices)))
    current = prices[-1]
    sup, res = support_resistance(prices)
    vol = volatility(prices)

    trend_7 = "haussier" if ma7 and current > ma7 else "baissier"
    trend_30 = "haussier" if ma30 and current > ma30 else "baissier"
    trend_90 = "haussier" if ma90 and current > ma90 else "baissier"
    confirmations = [trend_7, trend_30, trend_90].count("haussier")

    near_support = sup and current <= sup * 1.05
    near_resistance = res and current >= res * 0.95

    return {
        "coin": coin_id,
        "ma7": ma7,
        "ma30": ma30,
        "ma90": ma90,
        "rsi": rsi(prices),
        "macd": macd(prices),
        "trend_7": trend_7,
        "trend_30": trend_30,
        "trend_90": trend_90,
        "trend_confirmations": confirmations,
        "near_support": near_support,
        "near_resistance": near_resistance,
        "volatility": vol,
    }

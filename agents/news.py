import requests
import xml.etree.ElementTree as ET

NEGATIVE_KEYWORDS = [
    "ban", "hack", "crash", "sec", "lawsuit", "fraud", "scam",
    "regulation", "crackdown", "china ban", "collapse", "dump",
    "sell off", "bearish", "warning", "investigation", "arrested",
    "ponzi", "exploit", "vulnerability", "rug pull", "delisted"
]

POSITIVE_KEYWORDS = [
    "etf", "adoption", "bullish", "partnership", "launch", "all-time high",
    "ath", "rally", "surge", "buy", "institutional", "approved", "upgrade",
    "mainnet", "listing", "breakthrough", "record", "growth", "profit",
    "halving", "staking", "integration", "milestone"
]

COIN_SEARCH_TERMS = {
    "bitcoin": "bitcoin BTC",
    "ethereum": "ethereum ETH",
    "solana": "solana SOL",
    "dogecoin": "dogecoin DOGE",
    "shiba-inu": "shiba inu SHIB",
    "pepe": "pepe crypto",
    "bnb": "BNB binance coin",
    "xrp": "XRP ripple",
    "cardano": "cardano ADA",
    "sui": "sui crypto",
    "injective-protocol": "injective INJ",
    "render-token": "render RNDR",
    "fetch-ai": "fetch.ai FET",
}

def fetch_news(coin_id):
    search = COIN_SEARCH_TERMS.get(coin_id, coin_id)
    try:
        url = f"https://news.google.com/rss/search?q={search}+crypto&hl=en&gl=US&ceid=US:en"
        r = requests.get(url, timeout=10, headers={"User-Agent": "trading-bot/1.0"})
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
        titles = []
        for item in root.findall(".//item")[:10]:
            title = item.find("title")
            if title is not None and title.text:
                titles.append(title.text.lower())
        return titles
    except Exception as e:
        print(f"[News] Erreur {coin_id}: {e}")
    return []

def analyze_news(coin_id):
    titles = fetch_news(coin_id)
    if not titles:
        return {"coin": coin_id, "news_score": 0, "positive": 0, "negative": 0, "total": 0}

    positive = sum(1 for t in titles if any(kw in t for kw in POSITIVE_KEYWORDS))
    negative = sum(1 for t in titles if any(kw in t for kw in NEGATIVE_KEYWORDS))

    raw = positive - negative
    news_score = max(-50, min(50, raw * 10))

    sentiment = "positif" if news_score > 0 else "negatif" if news_score < 0 else "neutre"
    print(f"[News] {coin_id.upper()} — {positive} positives / {negative} negatives / Score: {news_score} ({sentiment})")

    return {
        "coin": coin_id,
        "news_score": news_score,
        "positive": positive,
        "negative": negative,
        "total": len(titles),
        "sentiment": sentiment,
    }

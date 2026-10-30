import requests

COIN_NAMES = {
    "bitcoin": ["bitcoin", "btc"],
    "ethereum": ["ethereum", "eth"],
    "solana": ["solana", "sol"],
    "dogecoin": ["dogecoin", "doge"],
    "shiba-inu": ["shiba", "shib"],
    "pepe": ["pepe"],
    "bonk": ["bonk"],
    "floki": ["floki"],
    "bnb": ["bnb", "binance"],
    "xrp": ["xrp", "ripple"],
    "cardano": ["cardano", "ada"],
    "sui": ["sui"],
    "aptos": ["aptos", "apt"],
    "arbitrum": ["arbitrum", "arb"],
    "injective-protocol": ["injective", "inj"],
    "render-token": ["render", "rndr"],
    "fetch-ai": ["fetch", "fet"],
}

def fetch_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        if r.status_code == 200:
            data = r.json()["data"][0]
            return int(data["value"]), data["value_classification"]
    except Exception as e:
        print(f"[Social] Erreur fear&greed: {e}")
    return 50, "Neutral"

def fetch_reddit_mentions(coin_id):
    keywords = COIN_NAMES.get(coin_id, [coin_id])
    total = 0
    try:
        headers = {"User-Agent": "trading-bot/1.0"}
        for kw in keywords[:2]:
            url = f"https://www.reddit.com/r/CryptoCurrency/search.json"
            params = {"q": kw, "sort": "hot", "t": "day", "limit": 25}
            r = requests.get(url, headers=headers, params=params, timeout=10)
            if r.status_code == 200:
                posts = r.json().get("data", {}).get("children", [])
                total += len(posts)
    except Exception as e:
        print(f"[Social] Erreur Reddit {coin_id}: {e}")
    return total

def get_social_score(coin_id):
    fear_value, fear_label = fetch_fear_greed()
    reddit_count = fetch_reddit_mentions(coin_id)

    # Score fear & greed (0-50 points)
    fear_score = fear_value / 2

    # Score Reddit (0-50 points, max 25 posts = 50 pts)
    reddit_score = min(reddit_count * 2, 50)

    buzz_score = int(fear_score + reddit_score)

    print(f"[Social] {coin_id.upper()} — Fear&Greed: {fear_value} ({fear_label}) | Reddit: {reddit_count} posts | Buzz: {buzz_score}/100")

    return {
        "coin": coin_id,
        "buzz_score": buzz_score,
        "fear_greed": fear_value,
        "fear_label": fear_label,
        "reddit_mentions": reddit_count,
    }

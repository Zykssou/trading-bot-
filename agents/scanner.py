import requests
import time
from datetime import datetime
from config import COINGECKO_API_URL, TRACKED_COINS, VOLUME_SPIKE_THRESHOLD, PRICE_CHANGE_THRESHOLD
from database.db import save_market_data, save_signal

def fetch_coin_data(coin_id):
    try:
        url = f"{COINGECKO_API_URL}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            market = data["market_data"]
            return {
                "coin": coin_id,
                "price": market["current_price"].get("usd", 0),
                "volume_24h": market["total_volume"].get("usd", 0),
                "price_change_1h": market["price_change_percentage_1h_in_currency"].get("usd", 0),
                "price_change_24h": market["price_change_percentage_24h"] or 0,
                "market_cap": market["market_cap"].get("usd", 0),
            }
    except Exception as e:
        print(f"[Scanner] Erreur pour {coin_id}: {e}")
    return None

def fetch_trending_coins():
    try:
        url = f"{COINGECKO_API_URL}/search/trending"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            trending = [item["item"]["id"] for item in data.get("coins", [])]
            return trending
    except Exception as e:
        print(f"[Scanner] Erreur trending: {e}")
    return []

def analyze_coin(coin_data, previous_data=None):
    signals = []
    score = 0
    reasons = []

    price_change_1h = coin_data.get("price_change_1h", 0) or 0
    price_change_24h = coin_data.get("price_change_24h", 0) or 0

    # Signal hausse rapide
    if price_change_1h >= PRICE_CHANGE_THRESHOLD:
        score += 30
        reasons.append(f"Hausse {price_change_1h:.1f}% en 1h")

    if price_change_24h >= 20:
        score += 20
        reasons.append(f"Hausse {price_change_24h:.1f}% en 24h")

    # Signal volume
    if previous_data and previous_data.get("volume_24h", 0) > 0:
        volume_ratio = coin_data["volume_24h"] / previous_data["volume_24h"]
        if volume_ratio >= VOLUME_SPIKE_THRESHOLD:
            score += 40
            reasons.append(f"Volume x{volume_ratio:.1f} vs hier")

    # Signal baisse (signal de vente)
    if price_change_1h <= -PRICE_CHANGE_THRESHOLD:
        score -= 30
        reasons.append(f"Baisse {price_change_1h:.1f}% en 1h")

    signal_type = "buy" if score >= 40 else "sell" if score <= -20 else "hold"

    return {
        "signal_type": signal_type,
        "score": score,
        "reason": " | ".join(reasons) if reasons else "Marché stable"
    }

def run_scanner(previous_data_store=None):
    print(f"[Scanner] Scan démarré à {datetime.now().strftime('%H:%M:%S')}")

    if previous_data_store is None:
        previous_data_store = {}

    results = []

    # Coins suivis + trending
    trending = fetch_trending_coins()
    all_coins = list(set(TRACKED_COINS + trending[:5]))

    for coin in all_coins:
        data = fetch_coin_data(coin)
        if not data:
            time.sleep(1)
            continue

        save_market_data(
            coin=data["coin"],
            price=data["price"],
            volume_24h=data["volume_24h"],
            price_change_1h=data["price_change_1h"],
            price_change_24h=data["price_change_24h"],
            market_cap=data["market_cap"]
        )

        analysis = analyze_coin(data, previous_data_store.get(coin))

        if analysis["signal_type"] != "hold":
            save_signal(coin, analysis["signal_type"], analysis["score"], analysis["reason"])
            print(f"[Scanner] SIGNAL {analysis['signal_type'].upper()} sur {coin} | Score: {analysis['score']} | {analysis['reason']}")
            results.append({**data, **analysis})

        previous_data_store[coin] = data
        time.sleep(1.5)  # évite de se faire bloquer par l'API

    print(f"[Scanner] Scan terminé — {len(results)} signal(s) détecté(s)")
    return results, previous_data_store

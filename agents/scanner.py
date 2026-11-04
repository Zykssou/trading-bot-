import requests
import time
import os
from datetime import datetime
from config import COINGECKO_API_URL, TRACKED_COINS, VOLUME_SPIKE_THRESHOLD, PRICE_CHANGE_THRESHOLD, BUYABLE_COINS, COIN_PROFILES
from database.db import save_market_data, save_signal

def fetch_all_coins_data(coin_ids):
    try:
        api_key = os.getenv("COINGECKO_API_KEY", "")
        headers = {"x-cg-demo-api-key": api_key} if api_key else {}

        url = f"{COINGECKO_API_URL}/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ",".join(coin_ids),
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1,
            "price_change_percentage": "1h,24h"
        }
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            results = {}
            for coin in response.json():
                results[coin["id"]] = {
                    "coin": coin["id"],
                    "price": coin["current_price"] or 0,
                    "volume_24h": coin["total_volume"] or 0,
                    "price_change_1h": coin.get("price_change_percentage_1h_in_currency") or 0,
                    "price_change_24h": coin.get("price_change_percentage_24h") or 0,
                    "market_cap": coin["market_cap"] or 0,
                }
            print(f"[Scanner] CoinGecko OK — {len(results)} coins")
            return results
        else:
            print(f"[Scanner] CoinGecko erreur {response.status_code}")
    except Exception as e:
        print(f"[Scanner] Erreur: {e}")
    return {}

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
    coin_id = coin_data.get("coin", "")
    profile = COIN_PROFILES.get(coin_id, {})
    threshold = profile.get("threshold", PRICE_CHANGE_THRESHOLD)

    # Signal hausse rapide
    if price_change_1h >= threshold:
        score += 30
        reasons.append(f"Hausse {price_change_1h:.1f}% en 1h")

    if price_change_24h >= 20:
        score += 20
        reasons.append(f"Hausse {price_change_24h:.1f}% en 24h")

    # Signal volume — confirmation obligatoire pour BUY
    volume_confirmed = False
    if previous_data and previous_data.get("volume_24h", 0) > 0:
        volume_ratio = coin_data["volume_24h"] / previous_data["volume_24h"]
        if volume_ratio >= VOLUME_SPIKE_THRESHOLD:
            score += 40
            volume_confirmed = True
            reasons.append(f"Volume x{volume_ratio:.1f} vs scan précédent")

    # Signal baisse (signal de vente)
    if price_change_1h <= -threshold:
        score -= 30
        reasons.append(f"Baisse {price_change_1h:.1f}% en 1h")

    coin_id = coin_data.get("coin", "")
    buyable = coin_id in BUYABLE_COINS

    if score >= 55 and buyable and volume_confirmed:
        signal_type = "buy"
    elif score <= -20:
        signal_type = "sell"
    else:
        signal_type = "hold"

    return {
        "signal_type": signal_type,
        "score": score,
        "reason": " | ".join(reasons) if reasons else "Marché stable",
        "volume_confirmed": volume_confirmed,
        "buyable": buyable,
    }

def run_scanner(previous_data_store=None, extra_coins=None):
    print(f"[Scanner] Scan démarré à {datetime.now().strftime('%H:%M:%S')}")

    if previous_data_store is None:
        previous_data_store = {}

    results = []

    # Coins de la config + coins des positions ouvertes (pour pouvoir les fermer)
    all_coins = list(set(TRACKED_COINS + (extra_coins or [])))

    # 1 seule requête pour tous les coins
    all_data = fetch_all_coins_data(all_coins)

    for coin in all_coins:
        data = all_data.get(coin)
        if not data:
            print(f"  {coin.upper():<15} — données indisponibles")
            continue

        save_market_data(
            coin=data["coin"],
            price=data["price"],
            volume_24h=data["volume_24h"],
            price_change_1h=data["price_change_1h"],
            price_change_24h=data["price_change_24h"],
            market_cap=data["market_cap"]
        )

        print(f"  {coin.upper():<15} Prix: ${data['price']:<12} | 1h: {data['price_change_1h']:+.2f}% | 24h: {data['price_change_24h']:+.2f}%")

        analysis = analyze_coin(data, previous_data_store.get(coin))

        if analysis["signal_type"] != "hold":
            save_signal(coin, analysis["signal_type"], analysis["score"], analysis["reason"])
            print(f"[Scanner] SIGNAL {analysis['signal_type'].upper()} sur {coin} | Score: {analysis['score']} | {analysis['reason']}")
            results.append({**data, **analysis})

        previous_data_store[coin] = data

    print(f"[Scanner] Scan terminé — {len(results)} signal(s) détecté(s)")
    return results, previous_data_store

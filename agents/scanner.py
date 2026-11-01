import requests
import json
import time
from datetime import datetime
from config import TRACKED_COINS, VOLUME_SPIKE_THRESHOLD, PRICE_CHANGE_THRESHOLD, BUYABLE_COINS, COIN_PROFILES, BINANCE_SYMBOLS
from database.db import save_market_data, save_signal

BINANCE_API = "https://api.binance.com/api/v3"

def fetch_all_coins_data(coin_ids):
    try:
        tradeable = [(c, BINANCE_SYMBOLS[c]) for c in coin_ids if c in BINANCE_SYMBOLS]
        if not tradeable:
            return {}

        symbols = [sym for _, sym in tradeable]
        reverse_map = {sym: cid for cid, sym in tradeable}

        # Formatage strict sans espaces pour Binance
        symbols_str = "[" + ",".join(f'"{s}"' for s in symbols) + "]"

        # 24h stats (prix + variation 24h + volume)
        r24 = requests.get(f"{BINANCE_API}/ticker/24hr?symbols={symbols_str}", timeout=15)
        # 1h stats (variation 1h)
        r1h = requests.get(f"{BINANCE_API}/ticker?symbols={symbols_str}&windowSize=1h", timeout=15)

        results = {}
        if r24.status_code == 200:
            for t in r24.json():
                cid = reverse_map.get(t["symbol"])
                if cid:
                    results[cid] = {
                        "coin": cid,
                        "price": float(t["lastPrice"]),
                        "volume_24h": float(t["quoteVolume"]),
                        "price_change_1h": 0,
                        "price_change_24h": float(t["priceChangePercent"]),
                        "market_cap": 0,
                    }

        if r1h.status_code == 200:
            for t in r1h.json():
                cid = reverse_map.get(t["symbol"])
                if cid and cid in results:
                    results[cid]["price_change_1h"] = float(t["priceChangePercent"])

        print(f"[Scanner] Binance OK — {len(results)}/{len(tradeable)} coins")
        return results

    except Exception as e:
        print(f"[Scanner] Erreur Binance: {e}")
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
            reasons.append(f"Volume x{volume_ratio:.1f} vs hier")
        elif volume_ratio >= 1.1:
            score += 10
            volume_confirmed = True
            reasons.append(f"Volume +{(volume_ratio-1)*100:.0f}%")

    # Signal baisse (signal de vente)
    if price_change_1h <= -threshold:
        score -= 30
        reasons.append(f"Baisse {price_change_1h:.1f}% en 1h")

    coin_id = coin_data.get("coin", "")
    buyable = coin_id in BUYABLE_COINS

    if score >= 40 and buyable and volume_confirmed:
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

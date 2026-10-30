import requests
import time
from datetime import datetime

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
INITIAL_BALANCE = 1000.0
PRICE_CHANGE_THRESHOLD = 1.0
STOP_LOSS_PERCENT = 0.08
TAKE_PROFIT_PERCENT = 0.20
MAX_TRADE_PERCENT = 0.05

COINS = ["bitcoin", "ethereum", "solana", "pepe", "shiba-inu", "floki"]

def fetch_hourly(coin_id):
    try:
        url = f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": 90}
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json().get("prices", [])
            print(f"  {len(data)} bougies horaires recuperees")
            return data
        else:
            print(f"  API erreur {r.status_code}")
    except Exception as e:
        print(f"[Backtest] Erreur {coin_id}: {e}")
    return []

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))][-period:]
    gains = [c for c in changes if c > 0]
    losses = [abs(c) for c in changes if c < 0]
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calculate_ma(prices, period):
    if len(prices) < period:
        return prices[-1] if prices else 0
    return sum(prices[-period:]) / period

def score_signal(price_change, prices_so_far):
    score = 0
    if price_change >= PRICE_CHANGE_THRESHOLD:
        score += 30
    rsi = calculate_rsi(prices_so_far)
    ma7  = calculate_ma(prices_so_far, 168)   # 7 jours en heures
    ma30 = calculate_ma(prices_so_far, 720)   # 30 jours en heures
    if ma7 > ma30:
        score += 20
    else:
        score -= 20
    if rsi < 30:
        score += 30
    elif rsi > 70:
        score -= 30
    return score, rsi

def run_backtest():
    print("=" * 60)
    print("  BACKTEST HORAIRE — 90 jours | Depart: 1 000 euros")
    print("=" * 60)

    balance = INITIAL_BALANCE
    total_wins = 0
    total_losses = 0
    all_trades = []
    peak_balance = INITIAL_BALANCE
    max_drawdown = 0.0

    for coin in COINS:
        print(f"\n[Backtest] Recuperation donnees {coin.upper()}...")
        raw = fetch_hourly(coin)
        time.sleep(3)

        if len(raw) < 50:
            print(f"  Pas assez de donnees pour {coin}")
            continue

        prices = [p[1] for p in raw]
        dates  = [datetime.fromtimestamp(p[0]/1000).strftime("%Y-%m-%d %Hh") for p in raw]

        position = None
        coin_wins = 0
        coin_losses = 0

        for i in range(24, len(prices)):
            current_price = prices[i]
            prev_price    = prices[i-1]
            price_change  = ((current_price - prev_price) / prev_price) * 100
            prices_so_far = prices[:i+1]
            date = dates[i]

            # Verifier stop-loss / take-profit heure par heure
            if position:
                entry = position["entry_price"]
                change = (current_price - entry) / entry

                if change <= -STOP_LOSS_PERCENT:
                    pnl = position["amount"] * change
                    balance += position["amount"] + pnl
                    coin_losses += 1
                    total_losses += 1
                    all_trades.append({
                        "coin": coin, "date_buy": position["date"],
                        "date_sell": date, "entry": entry,
                        "exit": current_price, "pnl": pnl,
                        "pct": change * 100, "result": "STOP-LOSS"
                    })
                    position = None

                elif change >= TAKE_PROFIT_PERCENT:
                    pnl = position["amount"] * change
                    balance += position["amount"] + pnl
                    coin_wins += 1
                    total_wins += 1
                    all_trades.append({
                        "coin": coin, "date_buy": position["date"],
                        "date_sell": date, "entry": entry,
                        "exit": current_price, "pnl": pnl,
                        "pct": change * 100, "result": "TAKE-PROFIT"
                    })
                    position = None

                if balance > peak_balance:
                    peak_balance = balance
                drawdown = (peak_balance - balance) / peak_balance * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

            # Filtre marché global — pas d'achat si BTC en panique
            btc_prices = prices_so_far  # approximation locale
            btc_change_now = price_change if coin == "bitcoin" else 0

            # Signal d'achat
            if not position and price_change >= PRICE_CHANGE_THRESHOLD and btc_change_now >= -1.5:
                score, rsi = score_signal(price_change, prices_so_far)
                if score >= 40:
                    trade_amount = balance * MAX_TRADE_PERCENT
                    if trade_amount >= 5:
                        balance -= trade_amount
                        position = {
                            "entry_price": current_price,
                            "amount": trade_amount,
                            "date": date,
                            "coin": coin
                        }

        # Fermer position encore ouverte
        if position:
            change = (prices[-1] - position["entry_price"]) / position["entry_price"]
            pnl = position["amount"] * change
            balance += position["amount"] + pnl
            if change >= 0:
                coin_wins += 1
                total_wins += 1
            else:
                coin_losses += 1
                total_losses += 1
            all_trades.append({
                "coin": coin, "date_buy": position["date"],
                "date_sell": dates[-1], "entry": position["entry_price"],
                "exit": prices[-1], "pnl": pnl,
                "pct": change * 100, "result": "OUVERT->FERME"
            })

        print(f"  {coin.upper()}: {coin_wins}W / {coin_losses}L")

    total_trades = total_wins + total_losses
    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    total_return = ((balance - INITIAL_BALANCE) / INITIAL_BALANCE) * 100

    print("\n" + "=" * 60)
    print("  RESULTATS DU BACKTEST")
    print("=" * 60)
    print(f"  Periode          : 90 derniers jours (horaire)")
    print(f"  Balance depart   : {INITIAL_BALANCE:.2f} euros")
    print(f"  Balance finale   : {balance:.2f} euros")
    print(f"  Rendement total  : {total_return:+.1f}%")
    print(f"  Trades totaux    : {total_trades}")
    print(f"  Taux de reussite : {win_rate:.1f}%")
    print(f"  Max drawdown     : -{max_drawdown:.1f}%")
    print("=" * 60)

    if all_trades:
        print("\n  DERNIERS TRADES :")
        for t in sorted(all_trades, key=lambda x: x["date_sell"])[-8:]:
            print(f"  {t['date_sell']} | {t['coin'].upper():<10} {t['pct']:+.1f}% | {t['pnl']:+.2f}€ | {t['result']}")

    print()

if __name__ == "__main__":
    run_backtest()

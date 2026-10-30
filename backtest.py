import requests
import time
from datetime import datetime, timezone

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
INITIAL_BALANCE = 1000.0
PRICE_CHANGE_THRESHOLD = 1.0
STOP_LOSS_PERCENT = 0.08
TAKE_PROFIT_PERCENT = 0.20
MAX_TRADE_PERCENT = 0.05

COINS = ["bitcoin", "ethereum", "solana", "dogecoin", "pepe"]

# Janvier 2025 → aujourd'hui
START_TS = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
END_TS   = int(datetime(2026, 10, 30, tzinfo=timezone.utc).timestamp())

def fetch_history(coin_id):
    try:
        url = f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": 365}
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json().get("prices", [])
            print(f"  {len(data)} points de données récupérés")
            return data
        else:
            print(f"  API erreur {r.status_code}")
    except Exception as e:
        print(f"[Backtest] Erreur fetch {coin_id}: {e}")
    return []

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    changes = changes[-period:]
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
    ma7  = calculate_ma(prices_so_far, 7)
    ma30 = calculate_ma(prices_so_far, 30)

    current = prices_so_far[-1]
    if ma7 > ma30:
        score += 20
    else:
        score -= 20

    if rsi < 30:
        score += 30
    elif rsi > 70:
        score -= 30

    return score, rsi, ma7, ma30

def run_backtest():
    print("=" * 60)
    print("  BACKTEST — 365 derniers jours | Départ: 1 000€")
    print("=" * 60)

    balance = INITIAL_BALANCE
    all_trades = []
    total_wins = 0
    total_losses = 0
    peak_balance = INITIAL_BALANCE
    max_drawdown = 0.0

    for coin in COINS:
        print(f"\n[Backtest] Récupération données {coin.upper()}...")
        raw = fetch_history(coin)
        time.sleep(2)

        if len(raw) < 30:
            print(f"  Pas assez de données pour {coin}")
            continue

        prices = [p[1] for p in raw]
        dates  = [datetime.fromtimestamp(p[0]/1000).strftime("%Y-%m-%d") for p in raw]

        position = None
        coin_wins = 0
        coin_losses = 0

        for i in range(30, len(prices)):
            current_price = prices[i]
            prev_price    = prices[i-1]
            price_change_pct = ((current_price - prev_price) / prev_price) * 100
            prices_so_far = prices[:i+1]
            date = dates[i]

            # Vérifier si position ouverte → stop-loss / take-profit
            if position:
                entry = position["entry_price"]
                change = (current_price - entry) / entry

                if change <= -STOP_LOSS_PERCENT or change >= TAKE_PROFIT_PERCENT:
                    pnl = position["amount"] * change
                    balance += position["amount"] + pnl

                    if change >= TAKE_PROFIT_PERCENT:
                        result = "WIN"
                        coin_wins += 1
                        total_wins += 1
                    else:
                        result = "LOSS"
                        coin_losses += 1
                        total_losses += 1

                    all_trades.append({
                        "coin": coin, "date_buy": position["date"],
                        "date_sell": date, "entry": entry,
                        "exit": current_price, "pnl": pnl,
                        "pct": change * 100, "result": result
                    })

                    if balance > peak_balance:
                        peak_balance = balance
                    drawdown = (peak_balance - balance) / peak_balance * 100
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown

                    position = None

            # Chercher signal d'achat
            if not position and price_change_pct >= PRICE_CHANGE_THRESHOLD:
                score, rsi, ma7, ma30 = score_signal(price_change_pct, prices_so_far)
                if score >= 50:
                    trade_amount = balance * MAX_TRADE_PERCENT
                    if trade_amount >= 10:
                        balance -= trade_amount
                        position = {
                            "coin": coin, "entry_price": current_price,
                            "amount": trade_amount, "date": date
                        }

        if position:
            pnl = position["amount"] * ((prices[-1] - position["entry_price"]) / position["entry_price"])
            balance += position["amount"] + pnl

    total_trades = total_wins + total_losses
    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    total_return = ((balance - INITIAL_BALANCE) / INITIAL_BALANCE) * 100

    print("\n" + "=" * 60)
    print("  RÉSULTATS DU BACKTEST")
    print("=" * 60)
    print(f"  Période         : 365 derniers jours")
    print(f"  Balance départ  : {INITIAL_BALANCE:.2f}€")
    print(f"  Balance finale  : {balance:.2f}€")
    print(f"  Rendement total : {total_return:+.1f}%")
    print(f"  Trades totaux   : {total_trades}")
    print(f"  Taux de réussite: {win_rate:.1f}%")
    print(f"  Max drawdown    : -{max_drawdown:.1f}%")
    print("=" * 60)

    # Afficher les 5 pires trades (crash)
    if all_trades:
        worst = sorted(all_trades, key=lambda x: x["pnl"])[:5]
        print("\n  TOP 5 PIRES TRADES (gestion du crash) :")
        for t in worst:
            print(f"  {t['date_sell']} | {t['coin'].upper():<10} {t['pct']:+.1f}% | {t['pnl']:+.2f}€")

    print()

if __name__ == "__main__":
    run_backtest()

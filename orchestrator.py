import time
from datetime import datetime
from database.db import init_db
from agents.scanner import run_scanner
from agents.scoring import calculate_score
from agents.history import analyze_history
from agents.social import get_social_score
from agents.news import analyze_news
from agents.risk import check_risk, check_positions_to_close
from agents.execution import execute_buy, execute_sell, execute_short
from agents.reporting import report_buy, report_sell, report_summary, report_signal, report_daily, report_short_open
from config import SCAN_INTERVAL_SECONDS, LARGE_CAPS, MEME_COINS
from database.db import get_open_positions, update_position_price

def run():
    print("=" * 50)
    print("  BOT DE TRADING SIMULÉ — DÉMARRAGE")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 50)

    init_db()

    previous_data_store = {}
    cycle = 0
    last_daily_report = None

    while True:
        cycle += 1
        print(f"\n--- Cycle #{cycle} | {datetime.now().strftime('%H:%M:%S')} ---")

        # 1. Scanner — récupère les données et signaux
        scanner_signals, previous_data_store = run_scanner(previous_data_store)

        # Prix actuels pour vérifier les positions
        current_prices = {
            data["coin"]: data["price"]
            for data in previous_data_store.values()
            if isinstance(data, dict) and "price" in data
        }

        # 2. Mettre à jour current_price + pnl de chaque position ouverte
        for pos in get_open_positions():
            pos_id, coin, amount, buy_price, _, _, _, _, _, position_type = pos
            price_now = current_prices.get(coin)
            if price_now:
                if position_type == 'short':
                    pnl_val = amount * (buy_price - price_now) / buy_price
                else:
                    pnl_val = amount * (price_now - buy_price) / buy_price
                update_position_price(pos_id, price_now, round(pnl_val, 4))

        # 3. Vérifier les positions à fermer (stop-loss / take-profit)
        positions_to_close = check_positions_to_close(current_prices)
        for pos in positions_to_close:
            result = execute_sell(pos["id"], pos["coin"], pos["price"], pos["pnl"])
            if result["success"]:
                report_sell(pos["coin"], pos["price"], pos["pnl"])

        # Filtre marché global — si BTC chute, on n'achète rien + on ferme tout
        btc_data = previous_data_store.get("bitcoin", {})
        btc_change = btc_data.get("price_change_1h", 0) if isinstance(btc_data, dict) else 0
        market_in_panic = btc_change <= -1.5
        if market_in_panic:
            print(f"[Orchestrateur] MARCHE EN PANIQUE (BTC {btc_change:+.1f}%) — fermeture positions + aucun achat")
            for pos in check_positions_to_close(current_prices, force_close=True):
                result = execute_sell(pos["id"], pos["coin"], pos["price"], pos["pnl"])
                if result["success"]:
                    report_sell(pos["coin"], pos["price"], pos["pnl"])

        # 3. Analyser les signaux
        for signal in scanner_signals:
            report_signal(signal)
            signal_type = signal.get("signal_type")

            # LONG (achat)
            if signal_type == "buy" and not market_in_panic:
                coin = signal.get("coin", "")

                open_positions = get_open_positions()
                open_coins = [p[1] for p in open_positions]
                open_large = sum(1 for c in open_coins if c in LARGE_CAPS)
                open_meme = sum(1 for c in open_coins if c in MEME_COINS)
                if coin in LARGE_CAPS and open_large >= 1:
                    print(f"[Orchestrateur] {coin} ignoré — 1 large cap déjà ouvert")
                    continue
                if coin in MEME_COINS and open_meme >= 2:
                    print(f"[Orchestrateur] {coin} ignoré — 2 meme coins déjà ouverts")
                    continue

                history = analyze_history(coin)
                social = get_social_score(coin)
                news = analyze_news(coin)

                scored = calculate_score(signal, intelligence_signal=social, history_signal=history, news_signal=news)
                if scored["recommendation"] != "buy":
                    print(f"[Orchestrateur] Signal {coin} rejeté: {scored['reasons']}")
                    continue

                price = signal.get("price", 0)
                if price <= 0:
                    continue

                risk = check_risk(scored["coin"], scored["final_score"], price)
                if not risk["approved"]:
                    print(f"[Orchestrateur] Trade refusé pour {coin}: {risk['reason']}")
                    continue

                result = execute_buy(
                    coin=coin,
                    trade_amount=risk["trade_amount"],
                    price=price,
                    stop_loss=risk["stop_loss"],
                    take_profit=risk["take_profit"]
                )

                if result["success"]:
                    report_buy(
                        coin=scored["coin"],
                        tokens=result["tokens"],
                        price=price,
                        amount_spent=result["amount_spent"],
                        stop_loss=risk["stop_loss"],
                        take_profit=risk["take_profit"]
                    )

            # SHORT (vente à découvert) sur signal SELL
            elif signal_type == "sell":
                coin = signal.get("coin", "")
                price = signal.get("price", 0)
                if price <= 0:
                    continue

                open_positions = get_open_positions()
                open_coins = [p[1] for p in open_positions]
                if coin in open_coins:
                    continue

                risk = check_risk(coin, 50, price)
                if not risk["approved"]:
                    continue

                stop_loss_short = price * (1 + 0.08)
                take_profit_short = price * (1 - 0.20)

                result = execute_short(
                    coin=coin,
                    trade_amount=risk["trade_amount"],
                    price=price,
                    stop_loss=stop_loss_short,
                    take_profit=take_profit_short
                )

                if result["success"]:
                    report_short_open(
                        coin=coin,
                        price=price,
                        amount_spent=result["amount_spent"],
                        stop_loss=stop_loss_short,
                        take_profit=take_profit_short
                    )

        # Rapport toutes les 10 cycles
        if cycle % 10 == 0:
            report_summary()

        # Rapport journalier à 20h
        now = datetime.now()
        today_str = now.strftime("%d/%m/%Y")
        if now.hour == 20 and last_daily_report != today_str:
            report_daily(today_str)
            last_daily_report = today_str

        print(f"[Orchestrateur] Prochain scan dans {SCAN_INTERVAL_SECONDS}s...")
        time.sleep(SCAN_INTERVAL_SECONDS)

if __name__ == "__main__":
    run()

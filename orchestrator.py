import time
from datetime import datetime
from database.db import init_db
from agents.scanner import run_scanner
from agents.scoring import calculate_score
from agents.history import analyze_history
from agents.social import get_social_score
from agents.news import analyze_news
from agents.risk import check_risk, check_positions_to_close
from agents.execution import execute_buy, execute_sell
from agents.reporting import report_buy, report_sell, report_summary, report_signal
from config import SCAN_INTERVAL_SECONDS

def run():
    print("=" * 50)
    print("  BOT DE TRADING SIMULÉ — DÉMARRAGE")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 50)

    init_db()

    previous_data_store = {}
    cycle = 0

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

        # 2. Vérifier les positions à fermer (stop-loss / take-profit)
        positions_to_close = check_positions_to_close(current_prices)
        for pos in positions_to_close:
            result = execute_sell(pos["id"], pos["coin"], pos["price"], pos["pnl"])
            if result["success"]:
                report_sell(pos["coin"], pos["price"], pos["pnl"])

        # 3. Analyser les signaux d'achat
        for signal in scanner_signals:
            report_signal(signal)

            if signal.get("signal_type") != "buy":
                continue

            coin = signal.get("coin", "")
            history = analyze_history(coin)
            social = get_social_score(coin)
            news = analyze_news(coin)

            # Scoring complet : technique + historique + social + news
            scored = calculate_score(signal, intelligence_signal=social, history_signal=history, news_signal=news)
            if scored["recommendation"] != "buy":
                print(f"[Orchestrateur] Signal {coin} rejeté après analyse: {scored['reasons']}")
                continue

            price = signal.get("price", 0)

            if price <= 0:
                continue

            # Vérification du risque
            risk = check_risk(scored["coin"], scored["final_score"], price)
            if not risk["approved"]:
                print(f"[Orchestrateur] Trade refusé pour {coin}: {risk['reason']}")
                continue

            # Exécution
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

        # Rapport toutes les 10 cycles
        if cycle % 10 == 0:
            report_summary()

        print(f"[Orchestrateur] Prochain scan dans {SCAN_INTERVAL_SECONDS}s...")
        time.sleep(SCAN_INTERVAL_SECONDS)

if __name__ == "__main__":
    run()

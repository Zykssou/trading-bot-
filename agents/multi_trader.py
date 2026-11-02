import random
from datetime import datetime
from database.db import (
    init_multi_traders_db, get_all_multi_traders, get_multi_trader,
    update_multi_trader_balance, get_multi_open_positions,
    open_multi_position, close_multi_position, update_multi_position_price,
    get_multi_trader_stats, get_multi_closed_trades
)

INITIAL_BALANCE = 1000.0

# (id, name, strategy_label, description, sl, tp, min_score, max_score_short,
#  allowed_coins, stake_pct, max_pos, req_vol_x2, long_only, short_only, panic_btc_threshold)
STRATEGIES = [
    (1,  "Trader 1",  "Base",          "Stratégie de référence",          0.05, 0.10, 40, -20, None,                                                             0.05, 5,  False, False, False, -1.5),
    (2,  "Trader 2",  "Conservateur",  "Blue chips, risque faible",       0.03, 0.06, 55, -30, ["bitcoin","ethereum","solana","bnb","xrp"],                       0.05, 3,  False, False, False, -1.0),
    (3,  "Trader 3",  "Agressif",      "Gros gains, gros risques",        0.08, 0.20, 35, -15, None,                                                             0.08, 5,  False, False, False, -2.0),
    (4,  "Trader 4",  "Scalper",       "Petites prises rapides",          0.02, 0.04, 45, -25, None,                                                             0.05, 8,  False, False, False, -1.5),
    (5,  "Trader 5",  "Patience",      "Attend les grands mouvements",    0.05, 0.25, 40, -20, None,                                                             0.05, 5,  False, False, False, -1.5),
    (6,  "Trader 6",  "Mème Only",     "Meme coins uniquement",           0.05, 0.15, 40, -20, ["pepe","shiba-inu","floki","bonk","wojak"],                       0.05, 5,  False, False, False, -2.0),
    (7,  "Trader 7",  "Blue Chip",     "BTC/ETH/SOL uniquement",          0.03, 0.08, 50, -25, ["bitcoin","ethereum","solana"],                                   0.07, 3,  False, False, False, -1.0),
    (8,  "Trader 8",  "Long Only",     "Pas de positions short",          0.05, 0.10, 40, 999, None,                                                             0.05, 5,  False, True,  False, -1.5),
    (9,  "Trader 9",  "Short Only",    "Uniquement vendeur à découvert",  0.08, 0.15, 999,-20, None,                                                             0.05, 5,  False, False, True,  -1.5),
    (10, "Trader 10", "Volume+",       "Volume x2 obligatoire",           0.05, 0.10, 40, -20, None,                                                             0.05, 5,  True,  False, False, -1.5),
    (11, "Trader 11", "Momentum Fort", "Signal très fort requis",         0.05, 0.12, 60, -30, None,                                                             0.06, 4,  False, False, False, -1.5),
    (12, "Trader 12", "Anti-Panique",  "Ignore le filtre BTC panic",      0.05, 0.10, 40, -20, None,                                                             0.05, 5,  False, False, False, -99.0),
    (13, "Trader 13", "Small Stake",   "Petites mises, très diversifié",  0.05, 0.10, 40, -20, None,                                                             0.02, 10, False, False, False, -1.5),
    (14, "Trader 14", "Big Stake",     "Grosse mise par trade",           0.05, 0.10, 40, -20, None,                                                             0.10, 3,  False, False, False, -1.5),
    (15, "Trader 15", "DeFi Focus",    "Tokens DeFi et IA uniquement",    0.05, 0.12, 35, -20, ["injective-protocol","render-token","fetch-ai","sui"],            0.05, 5,  False, False, False, -1.5),
    (16, "Trader 16", "SOL Eco",       "Écosystème Solana",               0.05, 0.12, 35, -20, ["solana","sui","bonk"],                                          0.07, 4,  False, False, False, -1.5),
    (17, "Trader 17", "Contre-Trend",  "Entre sur signaux faibles",       0.05, 0.10, 25, -15, None,                                                             0.05, 5,  False, False, False, -1.5),
    (18, "Trader 18", "Trend 24h",     "24h change ≥10% requis",          0.05, 0.10, 40, -20, None,                                                             0.05, 5,  False, False, False, -1.5),
    (19, "Trader 19", "Tight SL",      "Stop ultra serré -1.5%",          0.015,0.05, 40, -20, None,                                                             0.05, 6,  False, False, False, -1.5),
    (20, "Trader 20", "Wide Range",    "Laisse courir, stop -10%",        0.10, 0.30, 40, -20, None,                                                             0.05, 4,  False, False, False, -3.0),
    (21, "Trader 21", "Mid Risk",      "Équilibré risque/rendement",      0.04, 0.08, 42, -22, None,                                                             0.06, 5,  False, False, False, -1.5),
    (22, "Trader 22", "Gold Ratio",    "Ratio SL/TP 1:3",                 0.05, 0.15, 40, -20, None,                                                             0.05, 5,  False, False, False, -1.5),
    (23, "Trader 23", "Breakout",      "Score fort + volume confirmé",    0.05, 0.12, 55, -25, None,                                                             0.06, 4,  True,  False, False, -1.5),
    (24, "Trader 24", "Alt Season",    "Altcoins hors BTC/ETH",           0.05, 0.12, 40, -20, ["solana","cardano","sui","injective-protocol","render-token","fetch-ai","pepe","shiba-inu","floki","bonk"], 0.05, 5, False, False, False, -1.5),
    (25, "Trader 25", "Chaos",         "Seuil aléatoire chaque cycle",    0.05, 0.10, 30, -15, None,                                                             0.05, 5,  False, False, False, -1.5),
]

def setup_traders():
    """Initialise les 25 traders dans la DB si pas encore fait."""
    init_multi_traders_db()
    import sqlite3
    conn = sqlite3.connect("trading_bot.db")
    c = conn.cursor()
    for strat in STRATEGIES:
        tid, name, strategy, desc = strat[0], strat[1], strat[2], strat[3]
        c.execute("SELECT id FROM multi_traders WHERE id=?", (tid,))
        if not c.fetchone():
            c.execute(
                "INSERT INTO multi_traders (id,name,strategy,description,balance,start_balance,updated_at) VALUES (?,?,?,?,?,?,?)",
                (tid, name, strategy, desc, INITIAL_BALANCE, INITIAL_BALANCE, datetime.now().isoformat())
            )
    conn.commit()
    conn.close()
    print(f"[MultiTrader] {len(STRATEGIES)} traders initialisés")

def _get_strategy(trader_id):
    for s in STRATEGIES:
        if s[0] == trader_id:
            return s
    return None

def run_all_traders(scanner_signals, current_prices, btc_change_1h=0):
    """Exécute toutes les stratégies pour chaque signal du scan."""
    for strat in STRATEGIES:
        (tid, name, strategy, desc, sl, tp, min_score, max_score_short,
         allowed_coins, stake_pct, max_pos, req_vol_x2, long_only, short_only, panic_threshold) = strat

        trader = get_multi_trader(tid)
        if not trader:
            continue

        balance = trader["balance"]
        open_pos = get_multi_open_positions(tid)
        open_coins = [p["coin"] for p in open_pos]

        # Filtre panique BTC
        market_panic = btc_change_1h <= panic_threshold

        # Chaos: randomise le seuil
        effective_min_score = min_score
        if strategy == "Chaos":
            effective_min_score = random.randint(20, 60)

        # 1. Update prix positions ouvertes + check SL/TP
        for pos in open_pos:
            price_now = current_prices.get(pos["coin"])
            if not price_now:
                continue
            if pos["position_type"] == "short":
                pnl_val = pos["amount"] * (pos["buy_price"] - price_now) / pos["buy_price"]
            else:
                pnl_val = pos["amount"] * (price_now - pos["buy_price"]) / pos["buy_price"]
            update_multi_position_price(pos["id"], price_now, round(pnl_val, 4))

            # Check stop-loss
            if pos["position_type"] == "long":
                hit_sl = price_now <= pos["buy_price"] * (1 - sl)
                hit_tp = price_now >= pos["buy_price"] * (1 + tp)
            else:
                hit_sl = price_now >= pos["buy_price"] * (1 + sl)
                hit_tp = price_now <= pos["buy_price"] * (1 - tp)

            if hit_sl or hit_tp or (market_panic and strategy != "Anti-Panique"):
                close_multi_position(pos["id"], price_now, round(pnl_val, 4))
                update_multi_trader_balance(tid, balance + pos["amount"] + round(pnl_val, 4))
                balance = get_multi_trader(tid)["balance"]
                open_coins = [c for c in open_coins if c != pos["coin"]]
                reason = "SL" if hit_sl else ("TP" if hit_tp else "PANIC")
                print(f"[T{tid}] FERME {pos['coin'].upper()} ({reason}) PnL:{pnl_val:+.2f}€")

        # 2. Traiter les signaux
        if market_panic and strategy != "Anti-Panique":
            continue

        for signal in scanner_signals:
            coin = signal.get("coin", "")
            price = signal.get("price", 0)
            sig_type = signal.get("signal_type")
            score = signal.get("score", 0)
            vol_confirmed = signal.get("volume_confirmed", False)

            if price <= 0:
                continue
            if allowed_coins and coin not in allowed_coins:
                continue
            if coin in open_coins:
                continue
            if len(open_pos) >= max_pos:
                continue
            if req_vol_x2 and not vol_confirmed:
                continue

            # Trend 24h: besoin d'un change 24h ≥ 10%
            if strategy == "Trend 24h":
                if abs(signal.get("price_change_24h", 0)) < 10:
                    continue

            trade_amount = round(balance * stake_pct, 2)
            if trade_amount < 5 or balance < trade_amount:
                continue

            # LONG
            if sig_type == "buy" and score >= effective_min_score and not short_only:
                open_multi_position(tid, coin, trade_amount, price, "long",
                                    price * (1 - sl), price * (1 + tp))
                update_multi_trader_balance(tid, balance - trade_amount)
                balance -= trade_amount
                open_coins.append(coin)
                open_pos = get_multi_open_positions(tid)
                print(f"[T{tid}] LONG {coin.upper()} {trade_amount:.0f}€ à {price}")

            # SHORT
            elif sig_type == "sell" and score <= max_score_short and not long_only:
                open_multi_position(tid, coin, trade_amount, price, "short",
                                    price * (1 + sl), price * (1 - tp))
                update_multi_trader_balance(tid, balance - trade_amount)
                balance -= trade_amount
                open_coins.append(coin)
                open_pos = get_multi_open_positions(tid)
                print(f"[T{tid}] SHORT {coin.upper()} {trade_amount:.0f}€ à {price}")

def get_traders_summary():
    """Retourne un résumé de tous les traders pour l'API."""
    traders = get_all_multi_traders()
    result = []
    for t in traders:
        tid = t["id"]
        stats = get_multi_trader_stats(tid)
        open_pos = get_multi_open_positions(tid)
        invested = sum(p["amount"] for p in open_pos)
        unrealized = sum(p["pnl"] for p in open_pos)
        total_val = t["balance"] + invested + unrealized
        pnl = total_val - t["start_balance"]
        wr = round(stats["wins"] / stats["total"] * 100) if stats["total"] > 0 else 0
        strat = _get_strategy(tid)
        result.append({
            "id": tid,
            "name": t["name"],
            "strategy": t["strategy"],
            "description": t["description"],
            "balance": round(t["balance"], 2),
            "total_value": round(total_val, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl / t["start_balance"] * 100, 2),
            "open_positions": len(open_pos),
            "total_trades": stats["total"],
            "win_rate": wr,
            "stake_pct": strat[9] * 100 if strat else 5,
            "sl": strat[4] * 100 if strat else 5,
            "tp": strat[5] * 100 if strat else 10,
            "positions_detail": [
                {"coin": p["coin"], "position_type": p["position_type"],
                 "amount": round(p["amount"], 2), "pnl": round(p["pnl"], 4),
                 "buy_price": round(p["buy_price"], 6)}
                for p in open_pos
            ],
            "closed_trades": [
                {"coin": t["coin"], "position_type": t["position_type"],
                 "amount": round(t["amount"], 2), "buy_price": round(t["buy_price"] or 0, 6),
                 "close_price": round(t["close_price"] or 0, 6), "pnl": round(t["pnl"], 4),
                 "closed_at": (t["closed_at"] or "")[:16].replace("T", " ")}
                for t in get_multi_closed_trades(tid)
            ],
        })
    return result

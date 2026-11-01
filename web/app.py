import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trading_bot.db")
INITIAL_BALANCE = 1000

COIN_EXPLANATIONS = {
    "pepe": "meme coin ultra-volatil, suit les tendances sociales",
    "shiba-inu": "meme coin populaire, très sensible au buzz",
    "floki": "meme coin communautaire, mouvement rapide",
    "bonk": "meme coin Solana, très volatil",
    "wojak": "meme coin spéculatif, mouvements extrêmes",
    "bitcoin": "référence du marché, tendances lentes mais fiables",
    "ethereum": "plateforme DeFi, suit les cycles d'adoption",
    "solana": "blockchain rapide, sensible aux news tech",
    "bnb": "token Binance, suit l'activité de l'exchange",
    "xrp": "paiements internationaux, sensible aux régulations",
    "chainlink": "oracle blockchain, suit l'adoption DeFi",
    "sui": "blockchain nouvelle gen, forte volatilité",
    "injective-protocol": "DeFi avancé, niche mais volatil",
    "render-token": "IA + crypto, suit le buzz IA",
    "fetch-ai": "agent IA, très spéculatif",
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_chart_ohlc(coin_id):
    try:
        db = get_db()
        rows = db.execute("""
            SELECT price, volume_24h, recorded_at FROM market_data
            WHERE coin = ? AND recorded_at >= datetime('now', '-3 days')
            ORDER BY recorded_at ASC
        """, (coin_id,)).fetchall()
        db.close()

        if not rows:
            return []

        candles = {}
        for row in rows:
            dt = datetime.fromisoformat(row["recorded_at"])
            dt = dt.replace(second=0, microsecond=0)
            dt = dt.replace(minute=(dt.minute // 5) * 5)
            ts = int(dt.timestamp())
            p = row["price"]
            if ts not in candles:
                candles[ts] = {"time": ts, "open": p, "high": p, "low": p, "close": p, "volume": row["volume_24h"] or 0}
            else:
                candles[ts]["high"] = max(candles[ts]["high"], p)
                candles[ts]["low"] = min(candles[ts]["low"], p)
                candles[ts]["close"] = p

        return sorted(candles.values(), key=lambda x: x["time"])
    except Exception as e:
        print(f"[Chart] Erreur: {e}")
    return []

@app.route("/dashboard")
def dashboard():
    db = get_db()

    balance = db.execute("SELECT balance FROM portfolio WHERE id = 1").fetchone()
    balance = balance["balance"] if balance else INITIAL_BALANCE

    positions = db.execute("SELECT * FROM positions WHERE status = 'open' ORDER BY opened_at DESC").fetchall()

    invested = sum(p["amount"] for p in positions)
    unrealized_pnl = sum(p["pnl"] for p in positions)
    total_value = balance + invested + unrealized_pnl
    pnl = total_value - INITIAL_BALANCE
    pnl_pct = (pnl / INITIAL_BALANCE) * 100

    trades = db.execute("SELECT * FROM positions WHERE status = 'closed' ORDER BY closed_at DESC LIMIT 20").fetchall()
    total_trades = db.execute("SELECT COUNT(*) as c FROM positions WHERE status = 'closed'").fetchone()["c"]
    wins = db.execute("SELECT COUNT(*) as c FROM positions WHERE status = 'closed' AND pnl > 0").fetchone()["c"]
    win_rate = round(wins / total_trades * 100) if total_trades > 0 else 0
    signals = db.execute("SELECT * FROM signals ORDER BY created_at DESC LIMIT 10").fetchall()

    today = datetime.now().strftime("%Y-%m-%d")
    today_trades = db.execute("""
        SELECT COUNT(*) as c, SUM(pnl) as total_pnl FROM positions
        WHERE status = 'closed' AND closed_at LIKE ?
    """, (f"{today}%",)).fetchone()

    db.close()

    return render_template("dashboard.html",
        balance=balance, pnl=pnl, pnl_pct=pnl_pct,
        positions=positions, trades=trades,
        total_trades=total_trades, wins=wins, win_rate=win_rate,
        signals=signals,
        today_trades=today_trades["c"] or 0,
        today_pnl=today_trades["total_pnl"] or 0,
        last_update=datetime.now().strftime("%H:%M:%S"),
        coin_explanations=COIN_EXPLANATIONS
    )

@app.route("/position/<int:pos_id>")
def position_detail(pos_id):
    db = get_db()
    pos = db.execute("SELECT * FROM positions WHERE id = ?", (pos_id,)).fetchone()
    db.close()

    if not pos:
        return "Position introuvable", 404

    coin = pos["coin"]
    is_short = pos["position_type"] == "short" if "position_type" in pos.keys() else False
    pnl_pct = ((pos["current_price"] - pos["buy_price"]) / pos["buy_price"] * 100) if not is_short else ((pos["buy_price"] - pos["current_price"]) / pos["buy_price"] * 100)
    explanation = COIN_EXPLANATIONS.get(coin, "coin suivi par le bot")

    if is_short:
        action_text = f"Le bot a ouvert un SHORT sur {coin.upper()} car le prix baissait. Il gagne si le prix continue de baisser."
        take_profit_price = pos["buy_price"] * 0.80
        stop_loss_price = pos["buy_price"] * 1.08
    else:
        action_text = f"Le bot a acheté {coin.upper()} car plusieurs indicateurs signalaient une hausse. Il gagne si le prix monte."
        take_profit_price = pos["buy_price"] * 1.20
        stop_loss_price = pos["buy_price"] * 0.92

    chart_data = fetch_chart_ohlc(coin)

    return render_template("position.html",
        pos=pos, coin=coin, is_short=is_short,
        pnl_pct=pnl_pct, explanation=explanation,
        action_text=action_text,
        take_profit_price=take_profit_price,
        stop_loss_price=stop_loss_price,
        chart_data=chart_data
    )

@app.route("/")
@app.route("/office")
def office():
    db = get_db()
    balance = db.execute("SELECT balance FROM portfolio WHERE id = 1").fetchone()
    balance = balance["balance"] if balance else INITIAL_BALANCE
    positions = db.execute("SELECT * FROM positions WHERE status = 'open'").fetchall()
    invested = sum(p["amount"] for p in positions)
    unrealized_pnl = sum(p["pnl"] for p in positions)
    total_value = balance + invested + unrealized_pnl
    pnl = total_value - INITIAL_BALANCE
    total_trades = db.execute("SELECT COUNT(*) as c FROM positions WHERE status='closed'").fetchone()["c"]
    wins = db.execute("SELECT COUNT(*) as c FROM positions WHERE status='closed' AND pnl > 0").fetchone()["c"]
    win_rate = round(wins / total_trades * 100) if total_trades > 0 else 0
    db.close()
    return render_template("office.html",
        balance=balance, pnl=pnl,
        positions=positions, win_rate=win_rate
    )

@app.route("/api/agents")
def api_agents():
    db = get_db()
    balance_row = db.execute("SELECT balance FROM portfolio WHERE id = 1").fetchone()
    balance = balance_row["balance"] if balance_row else INITIAL_BALANCE
    positions = db.execute("SELECT * FROM positions WHERE status = 'open'").fetchall()
    invested = sum(p["amount"] for p in positions)
    unrealized_pnl = sum(p["pnl"] for p in positions)
    pnl = (balance + invested + unrealized_pnl) - INITIAL_BALANCE
    total_trades = db.execute("SELECT COUNT(*) as c FROM positions WHERE status='closed'").fetchone()["c"]
    wins = db.execute("SELECT COUNT(*) as c FROM positions WHERE status='closed' AND pnl > 0").fetchone()["c"]
    win_rate = round(wins / total_trades * 100) if total_trades > 0 else 0
    recent_signals = db.execute("SELECT * FROM signals ORDER BY created_at DESC LIMIT 5").fetchall()
    market_quiet = db.execute(
        "SELECT COUNT(*) as c FROM signals WHERE created_at >= datetime('now', '-20 minutes')"
    ).fetchone()["c"] == 0
    last_scan = db.execute("SELECT recorded_at FROM market_data ORDER BY recorded_at DESC LIMIT 1").fetchone()
    coins_scanned = db.execute(
        "SELECT COUNT(DISTINCT coin) as c FROM market_data WHERE recorded_at >= datetime('now', '-20 minutes')"
    ).fetchone()["c"]
    signals_1h = db.execute(
        "SELECT COUNT(*) as c FROM signals WHERE created_at >= datetime('now', '-1 hour')"
    ).fetchone()["c"]
    last_trades = db.execute("SELECT * FROM positions WHERE status='closed' ORDER BY closed_at DESC LIMIT 3").fetchall()
    last_scan_str = last_scan["recorded_at"][11:16] if last_scan else "—"
    large_caps = ["bitcoin","ethereum","solana","bnb","xrp","cardano","avalanche-2","chainlink"]
    nb_large = sum(1 for p in positions if p["coin"] in large_caps)

    def sig_logs(signals):
        out = []
        for s in signals[:4]:
            t = s["created_at"][11:16] if s["created_at"] else "—"
            out.append({"text": f"[{t}] {s['coin'].upper()} {s['signal_type'].upper()} score:{s['score']}"})
        return out or [{"text": "Aucun signal récent"}]

    total_value = balance + invested + unrealized_pnl
    data = {
        "_stats": {"balance": balance, "pnl": pnl, "total_value": total_value, "invested": invested, "unrealized_pnl": unrealized_pnl, "positions": len(positions), "win_rate": win_rate, "total_trades": total_trades},
        "_market_quiet": market_quiet,
        "scanner": {
            "role": "Surveillance des marchés crypto",
            "info": [
                {"label": "Dernier scan", "value": last_scan_str, "highlight": True},
                {"label": "Coins scannés (20min)", "value": str(coins_scanned)},
                {"label": "Signaux détectés (1h)", "value": str(signals_1h), "highlight": signals_1h > 0},
                {"label": "Intervalle", "value": "10 minutes"},
                {"label": "Source", "value": "CoinGecko Demo"},
            ],
            "logs": [
                {"text": f"[{last_scan_str}] Scan terminé — {coins_scanned} coins"},
                {"text": f"[Scanner] {signals_1h} signal(s) cette heure"},
                {"text": "[Scanner] Trending coins désactivés"},
            ],
        },
        "analyste": {
            "role": "Analyse technique et scoring",
            "info": [
                {"label": "Signaux actifs (1h)", "value": str(signals_1h), "highlight": signals_1h > 0},
                {"label": "Seuil BUY", "value": "score ≥ 40 + volume"},
                {"label": "Seuil SHORT", "value": "score ≤ -20"},
                {"label": "Confirmation volume", "value": "Obligatoire (×1.5)"},
                {"label": "Hausse min", "value": "Threshold par coin"},
            ],
            "logs": sig_logs(recent_signals),
        },
        "trader": {
            "role": "Exécution des ordres de trading",
            "info": [
                {"label": "Positions ouvertes", "value": str(len(positions)), "highlight": len(positions) > 0},
                {"label": "Balance liquide", "value": f"{balance:.2f}€", "highlight": True},
                {"label": "P&L latent", "value": f"{unrealized_pnl:+.2f}€", "highlight": True},
                {"label": "Trades fermés", "value": str(total_trades)},
                {"label": "Win rate", "value": f"{win_rate}%", "highlight": win_rate >= 50},
            ],
            "logs": (
                [{"text": f"[OPEN] {p['coin'].upper()} {p['position_type'].upper()} PnL:{p['pnl']:+.2f}€"} for p in positions[:3]] +
                [{"text": f"[FERMÉ] {t['coin'].upper()} {t['pnl']:+.2f}€"} for t in last_trades[:2]]
            ) or [{"text": "Aucun trade actif"}],
        },
        "risk": {
            "role": "Contrôle du risque et paramètres SL/TP",
            "info": [
                {"label": "Stop-loss global", "value": "-5%"},
                {"label": "Take-profit global", "value": "+10%"},
                {"label": "Max positions", "value": "5"},
                {"label": "Max meme coins", "value": "2"},
                {"label": "Panic BTC filter", "value": "-1.5% en 1h → ferme tout"},
            ],
            "logs": [
                {"text": f"[Risk] {len(positions)}/5 positions actives"},
                {"text": "[Risk] Anti-corrélation: max 1 large cap + 2 meme"},
                {"text": "[Risk] Filtres BUYABLE_COINS actifs"},
            ],
        },
        "portfolio": {
            "role": "Gestion du portefeuille et allocation",
            "info": [
                {"label": "Balance liquide", "value": f"{balance:.2f}€", "highlight": True},
                {"label": "Investi", "value": f"{invested:.2f}€"},
                {"label": "Valeur totale", "value": f"{balance+invested+unrealized_pnl:.2f}€", "highlight": True},
                {"label": "P&L total", "value": f"{pnl:+.2f}€", "highlight": True},
                {"label": "Large caps ouverts", "value": str(nb_large)},
            ],
            "logs": (
                [{"text": f"[POS] {p['coin'].upper()} {p['position_type'].upper()} {p['amount']:.0f}€ PnL:{p['pnl']:+.2f}€"} for p in positions[:4]]
            ) or [{"text": "Aucune position ouverte"}],
        },
        "reporter": {
            "role": "Alertes Telegram en temps réel",
            "info": [
                {"label": "Bot Telegram", "value": "Actif ✓", "highlight": True},
                {"label": "Dernier signal", "value": recent_signals[0]["created_at"][11:16] if recent_signals else "—"},
                {"label": "Signaux envoyés (1h)", "value": str(signals_1h), "highlight": signals_1h > 0},
                {"label": "Chat ID", "value": "****432120"},
            ],
            "logs": sig_logs(recent_signals),
        },
    }
    db.close()
    return jsonify(data)

@app.route("/api/chart/<coin>")
def api_chart(coin):
    data = fetch_chart_ohlc(coin)
    return jsonify(data)

@app.route("/api/traders")
def api_traders():
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from agents.multi_trader import get_traders_summary, setup_traders
        from database.db import init_multi_traders_db
        init_multi_traders_db()
        setup_traders()
        return jsonify(get_traders_summary())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

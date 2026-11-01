import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify
import sqlite3
import requests
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

def fetch_chart_data(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        r = requests.get(url, params={"vs_currency": "usd", "days": 7}, timeout=10)
        if r.status_code == 200:
            prices = r.json().get("prices", [])
            return [{"t": p[0], "p": p[1]} for p in prices[-168:]]
    except:
        pass
    return []

@app.route("/")
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

    chart_data = fetch_chart_data(coin)

    return render_template("position.html",
        pos=pos, coin=coin, is_short=is_short,
        pnl_pct=pnl_pct, explanation=explanation,
        action_text=action_text,
        take_profit_price=take_profit_price,
        stop_loss_price=stop_loss_price,
        chart_data=chart_data
    )

if __name__ == "__main__":
    app.run(debug=True)

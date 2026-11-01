import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trading_bot.db")
INITIAL_BALANCE = 1000

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def dashboard():
    db = get_db()

    balance = db.execute("SELECT balance FROM portfolio WHERE id = 1").fetchone()
    balance = balance["balance"] if balance else INITIAL_BALANCE

    positions = db.execute("SELECT * FROM positions WHERE status = 'open' ORDER BY opened_at DESC").fetchall()

    # P&L réel = cash dispo + valeur positions ouvertes - mise initiale
    invested = sum(p["amount"] for p in positions)
    unrealized_pnl = sum(p["pnl"] for p in positions)
    total_value = balance + invested + unrealized_pnl
    pnl = total_value - INITIAL_BALANCE
    pnl_pct = (pnl / INITIAL_BALANCE) * 100

    trades = db.execute("""
        SELECT * FROM positions WHERE status = 'closed'
        ORDER BY closed_at DESC LIMIT 20
    """).fetchall()

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
        balance=balance,
        pnl=pnl,
        pnl_pct=pnl_pct,
        positions=positions,
        trades=trades,
        total_trades=total_trades,
        wins=wins,
        win_rate=win_rate,
        signals=signals,
        today_trades=today_trades["c"] or 0,
        today_pnl=today_trades["total_pnl"] or 0,
        last_update=datetime.now().strftime("%H:%M:%S")
    )

if __name__ == "__main__":
    app.run(debug=True)

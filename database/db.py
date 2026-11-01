import sqlite3
import json
from datetime import datetime

DB_PATH = "trading_bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY,
            balance REAL,
            updated_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin TEXT,
            amount REAL,
            buy_price REAL,
            current_price REAL,
            pnl REAL,
            status TEXT,
            opened_at TEXT,
            closed_at TEXT,
            position_type TEXT DEFAULT 'long'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin TEXT,
            signal_type TEXT,
            score INTEGER,
            reason TEXT,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin TEXT,
            price REAL,
            volume_24h REAL,
            price_change_1h REAL,
            price_change_24h REAL,
            market_cap REAL,
            recorded_at TEXT
        )
    """)

    # Portefeuille initial si vide
    from config import INITIAL_BALANCE
    c.execute("SELECT COUNT(*) FROM portfolio")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO portfolio (balance, updated_at) VALUES (?, ?)",
                  (INITIAL_BALANCE, datetime.now().isoformat()))

    conn.commit()
    conn.close()

def get_balance():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM portfolio WHERE id = 1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else 10000

def update_balance(new_balance):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE portfolio SET balance = ?, updated_at = ? WHERE id = 1",
              (new_balance, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_market_data(coin, price, volume_24h, price_change_1h, price_change_24h, market_cap):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO market_data (coin, price, volume_24h, price_change_1h, price_change_24h, market_cap, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (coin, price, volume_24h, price_change_1h, price_change_24h, market_cap, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_signal(coin, signal_type, score, reason):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO signals (coin, signal_type, score, reason, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (coin, signal_type, score, reason, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def update_position_price(position_id, current_price, pnl):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE positions SET current_price = ?, pnl = ? WHERE id = ?",
              (current_price, pnl, position_id))
    conn.commit()
    conn.close()

def get_open_positions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, coin, amount, buy_price, current_price, pnl, status, opened_at, closed_at, position_type FROM positions WHERE status = 'open'")
    rows = c.fetchall()
    conn.close()
    return rows

def open_position(coin, amount, buy_price, position_type='long'):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO positions (coin, amount, buy_price, current_price, pnl, status, opened_at, position_type)
        VALUES (?, ?, ?, ?, 0, 'open', ?, ?)
    """, (coin, amount, buy_price, buy_price, datetime.now().isoformat(), position_type))
    conn.commit()
    conn.close()

def close_position(position_id, close_price, pnl):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE positions SET status = 'closed', current_price = ?, pnl = ?, closed_at = ?
        WHERE id = ?
    """, (close_price, pnl, datetime.now().isoformat(), position_id))
    conn.commit()
    conn.close()

def get_today_trades():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("""
        SELECT coin, pnl, closed_at FROM positions
        WHERE status = 'closed' AND closed_at LIKE ?
    """, (f"{today}%",))
    rows = c.fetchall()
    conn.close()
    return rows

def get_recent_signals(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM signals ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

# ──────────────────────────────────────────────
#  MULTI-TRADER DB FUNCTIONS
# ──────────────────────────────────────────────

def init_multi_traders_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS multi_traders (
            id INTEGER PRIMARY KEY,
            name TEXT,
            strategy TEXT,
            description TEXT,
            balance REAL DEFAULT 1000,
            start_balance REAL DEFAULT 1000,
            updated_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS multi_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trader_id INTEGER,
            coin TEXT,
            amount REAL,
            buy_price REAL,
            current_price REAL DEFAULT 0,
            stop_loss REAL,
            take_profit REAL,
            pnl REAL DEFAULT 0,
            status TEXT DEFAULT 'open',
            position_type TEXT DEFAULT 'long',
            opened_at TEXT,
            closed_at TEXT,
            close_price REAL
        )
    """)
    conn.commit()
    conn.close()

def get_all_multi_traders():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM multi_traders ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def get_multi_trader(trader_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM multi_traders WHERE id = ?", (trader_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_multi_trader_balance(trader_id, balance):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE multi_traders SET balance = ?, updated_at = ? WHERE id = ?",
              (balance, datetime.now().isoformat(), trader_id))
    conn.commit()
    conn.close()

def get_multi_open_positions(trader_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM multi_positions WHERE trader_id = ? AND status = 'open'", (trader_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def open_multi_position(trader_id, coin, amount, buy_price, position_type, stop_loss, take_profit):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO multi_positions
        (trader_id, coin, amount, buy_price, current_price, stop_loss, take_profit, pnl, status, position_type, opened_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'open', ?, ?)
    """, (trader_id, coin, amount, buy_price, buy_price, stop_loss, take_profit, position_type, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def close_multi_position(pos_id, close_price, pnl):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE multi_positions SET status='closed', current_price=?, pnl=?, close_price=?, closed_at=?
        WHERE id=?
    """, (close_price, pnl, close_price, datetime.now().isoformat(), pos_id))
    conn.commit()
    conn.close()

def update_multi_position_price(pos_id, current_price, pnl):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE multi_positions SET current_price=?, pnl=? WHERE id=?",
              (current_price, pnl, pos_id))
    conn.commit()
    conn.close()

def get_multi_trader_stats(trader_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total, SUM(CASE WHEN pnl>0 THEN 1 ELSE 0 END) as wins, SUM(pnl) as total_pnl FROM multi_positions WHERE trader_id=? AND status='closed'", (trader_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {"total":0,"wins":0,"total_pnl":0}

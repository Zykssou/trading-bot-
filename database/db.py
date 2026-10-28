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
            closed_at TEXT
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
    c.execute("SELECT COUNT(*) FROM portfolio")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO portfolio (balance, updated_at) VALUES (10000, ?)",
                  (datetime.now().isoformat(),))

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

def get_open_positions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM positions WHERE status = 'open'")
    rows = c.fetchall()
    conn.close()
    return rows

def open_position(coin, amount, buy_price):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO positions (coin, amount, buy_price, current_price, pnl, status, opened_at)
        VALUES (?, ?, ?, ?, 0, 'open', ?)
    """, (coin, amount, buy_price, buy_price, datetime.now().isoformat()))
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

def get_recent_signals(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM signals ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

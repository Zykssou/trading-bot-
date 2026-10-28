import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from database.db import get_balance, get_open_positions, get_recent_signals

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[Telegram] {message}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[Telegram] Erreur envoi: {e}")

def report_buy(coin, tokens, price, amount_spent, stop_loss, take_profit):
    msg = (
        f"🟢 *ACHAT — {coin.upper()}*\n"
        f"Prix: `{price}$`\n"
        f"Mise: `{amount_spent}$` → `{tokens:.6f}` tokens\n"
        f"Stop-loss: `{stop_loss}$`\n"
        f"Take-profit: `{take_profit}$`\n"
        f"Balance: `{get_balance():.2f}$`"
    )
    send_telegram(msg)

def report_sell(coin, close_price, pnl):
    emoji = "✅" if pnl >= 0 else "❌"
    msg = (
        f"{emoji} *VENTE — {coin.upper()}*\n"
        f"Prix: `{close_price}$`\n"
        f"P&L: `{pnl:+.2f}$`\n"
        f"Balance: `{get_balance():.2f}$`"
    )
    send_telegram(msg)

def report_summary():
    balance = get_balance()
    positions = get_open_positions()
    signals = get_recent_signals(5)

    pnl_total = balance - 10000

    msg = (
        f"📊 *RAPPORT DU BOT*\n"
        f"Balance: `{balance:.2f}$`\n"
        f"P&L total: `{pnl_total:+.2f}$`\n"
        f"Positions ouvertes: `{len(positions)}`\n"
        f"Derniers signaux: `{len(signals)}`"
    )
    send_telegram(msg)

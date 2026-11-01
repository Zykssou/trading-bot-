import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from database.db import get_balance, get_open_positions, get_recent_signals, get_today_trades
from config import INITIAL_BALANCE

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

    pnl_total = balance - INITIAL_BALANCE

    msg = (
        f"📊 *RAPPORT DU BOT*\n"
        f"Balance: `{balance:.2f}$`\n"
        f"P&L total: `{pnl_total:+.2f}$`\n"
        f"Positions ouvertes: `{len(positions)}`\n"
        f"Derniers signaux: `{len(signals)}`"
    )
    send_telegram(msg)
def report_daily(date_str):
    trades = get_today_trades()
    balance = get_balance()
    pnl_total = balance - INITIAL_BALANCE
    pnl_pct = (pnl_total / INITIAL_BALANCE) * 100

    wins = [t for t in trades if t[1] > 0]
    losses = [t for t in trades if t[1] <= 0]
    win_rate = (len(wins) / len(trades) * 100) if trades else 0
    gain_jour = sum(t[1] for t in trades)

    msg = (
        f"📅 *RAPPORT JOURNALIER — {date_str}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Trades aujourd'hui: `{len(trades)}`\n"
        f"✅ Gagnants: `{len(wins)}` | ❌ Perdants: `{len(losses)}`\n"
        f"Taux de réussite: `{win_rate:.0f}%`\n"
        f"Gain du jour: `{gain_jour:+.2f}€`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Balance totale: `{balance:.2f}€`\n"
        f"P&L global: `{pnl_total:+.2f}€` ({pnl_pct:+.1f}%)"
    )
    send_telegram(msg)

def report_signal(s):
    t=s.get('signal_type','')
    coin=s.get('coin','').upper()
    send_telegram('SIGNAL '+t.upper()+' '+coin)

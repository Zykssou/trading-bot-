from config import MAX_TRADE_PERCENT, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT, MAX_DAILY_LOSS_PERCENT
from database.db import get_balance, get_open_positions

def check_risk(coin, score, price):
    balance = get_balance()
    open_positions = get_open_positions()

    # Pas plus de 5 positions ouvertes en même temps
    if len(open_positions) >= 5:
        return {"approved": False, "reason": "Trop de positions ouvertes (max 5)"}

    # Pas de doublon sur le même coin
    open_coins = [p[1] for p in open_positions]
    if coin in open_coins:
        return {"approved": False, "reason": f"Position déjà ouverte sur {coin}"}

    # Calcul de la mise
    trade_amount = balance * MAX_TRADE_PERCENT

    if trade_amount < 10:
        return {"approved": False, "reason": "Balance trop faible"}

    stop_loss_price = price * (1 - STOP_LOSS_PERCENT)
    take_profit_price = price * (1 + TAKE_PROFIT_PERCENT)

    return {
        "approved": True,
        "trade_amount": round(trade_amount, 2),
        "stop_loss": round(stop_loss_price, 6),
        "take_profit": round(take_profit_price, 6),
        "reason": "Risque validé"
    }

def check_positions_to_close(current_prices):
    open_positions = get_open_positions()
    to_close = []

    for position in open_positions:
        pos_id, coin, amount, buy_price, current_price, pnl, status, opened_at, closed_at = position
        price_now = current_prices.get(coin)

        if not price_now:
            continue

        pnl_pct = (price_now - buy_price) / buy_price

        if pnl_pct <= -STOP_LOSS_PERCENT:
            to_close.append({
                "id": pos_id,
                "coin": coin,
                "reason": f"Stop-loss déclenché ({pnl_pct*100:.1f}%)",
                "price": price_now,
                "pnl": (price_now - buy_price) * amount / buy_price
            })
        elif pnl_pct >= TAKE_PROFIT_PERCENT:
            to_close.append({
                "id": pos_id,
                "coin": coin,
                "reason": f"Take-profit atteint ({pnl_pct*100:.1f}%)",
                "price": price_now,
                "pnl": (price_now - buy_price) * amount / buy_price
            })

    return to_close

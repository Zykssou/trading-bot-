from database.db import open_position, close_position, update_balance, get_balance

def execute_short(coin, trade_amount, price, stop_loss, take_profit):
    balance = get_balance()
    if balance < trade_amount:
        return {"success": False, "reason": "Balance insuffisante"}

    open_position(coin, trade_amount, price, position_type='short')
    update_balance(balance - trade_amount)

    print(f"[Execution] SHORT {coin} | Mise: {trade_amount}$ à {price}$")
    print(f"[Execution] Stop-loss: {stop_loss}$ | Take-profit: {take_profit}$")

    return {
        "success": True,
        "coin": coin,
        "price": price,
        "amount_spent": trade_amount,
        "stop_loss": stop_loss,
        "take_profit": take_profit
    }

def execute_buy(coin, trade_amount, price, stop_loss, take_profit):
    balance = get_balance()

    if balance < trade_amount:
        return {"success": False, "reason": "Balance insuffisante"}

    tokens = trade_amount / price
    open_position(coin, trade_amount, price)  # on stocke les euros, pas les tokens
    update_balance(balance - trade_amount)

    print(f"[Execution] ACHAT {coin} | {tokens:.6f} tokens à {price}$ | Mise: {trade_amount}$")
    print(f"[Execution] Stop-loss: {stop_loss}$ | Take-profit: {take_profit}$")

    return {
        "success": True,
        "coin": coin,
        "tokens": tokens,
        "price": price,
        "amount_spent": trade_amount,
        "stop_loss": stop_loss,
        "take_profit": take_profit
    }

def execute_sell(position_id, coin, close_price, pnl):
    from database.db import get_open_positions
    positions = get_open_positions()
    amount = next((p[2] for p in positions if p[0] == position_id), 0)
    balance = get_balance()
    close_position(position_id, close_price, pnl)
    update_balance(balance + amount + pnl)

    result = "PROFIT" if pnl >= 0 else "PERTE"
    print(f"[Execution] VENTE {coin} | {result}: {pnl:+.2f}$ | Prix: {close_price}$")

    return {
        "success": True,
        "coin": coin,
        "close_price": close_price,
        "pnl": pnl
    }

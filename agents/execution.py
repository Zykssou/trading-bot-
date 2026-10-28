from database.db import open_position, close_position, update_balance, get_balance

def execute_buy(coin, trade_amount, price, stop_loss, take_profit):
    balance = get_balance()

    if balance < trade_amount:
        return {"success": False, "reason": "Balance insuffisante"}

    # Calcul des tokens achetés
    tokens = trade_amount / price

    open_position(coin, tokens, price)
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
    balance = get_balance()
    close_position(position_id, close_price, pnl)
    update_balance(balance + pnl)

    result = "PROFIT" if pnl >= 0 else "PERTE"
    print(f"[Execution] VENTE {coin} | {result}: {pnl:+.2f}$ | Prix: {close_price}$")

    return {
        "success": True,
        "coin": coin,
        "close_price": close_price,
        "pnl": pnl
    }

import sqlite3

DB_PATH = "trading_bot.db"

def get_coin_learning_adjustment(coin):
    """Pénalise les coins qui perdent souvent, booste ceux qui gagnent."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Derniers 20 trades sur ce coin (toutes sources)
        c.execute("""
            SELECT pnl FROM (
                SELECT pnl FROM positions WHERE coin=? AND status='closed'
                UNION ALL
                SELECT pnl FROM multi_positions WHERE coin=? AND status='closed'
            ) ORDER BY rowid DESC LIMIT 20
        """, (coin, coin))
        rows = c.fetchall()
        conn.close()

        if len(rows) < 5:
            return 0  # pas assez de données

        wins = sum(1 for r in rows if r[0] > 0)
        wr = wins / len(rows)

        if wr < 0.25:
            return -30  # ce coin perd souvent → forte pénalité
        elif wr < 0.40:
            return -15  # résultats médiocres
        elif wr > 0.65:
            return +15  # ce coin performe bien → bonus
        return 0
    except Exception:
        return 0

def calculate_score(scanner_signal, intelligence_signal=None, history_signal=None, news_signal=None):
    score = scanner_signal.get("score", 0)
    reasons = [scanner_signal.get("reason", "")]
    coin = scanner_signal.get("coin", "")

    if history_signal:
        rsi_val = history_signal.get("rsi")
        macd_val = history_signal.get("macd")
        confirmations = history_signal.get("trend_confirmations", 0)
        near_support = history_signal.get("near_support", False)
        near_resistance = history_signal.get("near_resistance", False)
        vol = history_signal.get("volatility")

        # Tendance multi-timeframe
        if confirmations == 3:
            score += 30
            reasons.append("Tendance haussiere 7j+30j+90j")
        elif confirmations == 2:
            score += 15
            reasons.append("Tendance haussiere 2/3 TF")
        elif confirmations == 1:
            score -= 10
            reasons.append("Tendance mixte")
        else:
            score -= 25
            reasons.append("Tendance baissiere tous TF")

        # Support / resistance
        if near_support:
            score += 20
            reasons.append("Prix pres du support")
        if near_resistance:
            score -= 20
            reasons.append("Prix pres de la resistance")

        # RSI — ne pas acheter si RSI > 60 (déjà surachat)
        if rsi_val is not None:
            if rsi_val < 30:
                score += 30
                reasons.append(f"RSI survente ({rsi_val:.0f})")
            elif rsi_val < 45:
                score += 10
                reasons.append(f"RSI neutre bas ({rsi_val:.0f})")
            elif rsi_val > 70:
                score -= 35
                reasons.append(f"RSI surachat ({rsi_val:.0f})")
            elif rsi_val > 60:
                score -= 20
                reasons.append(f"RSI eleve ({rsi_val:.0f})")

        # MACD
        if macd_val is not None:
            if macd_val > 0:
                score += 15
                reasons.append("MACD positif")
            else:
                score -= 10
                reasons.append("MACD negatif")

        # Volatilite trop haute = risque
        if vol is not None and vol > 15:
            score -= 10
            reasons.append(f"Volatilite elevee ({vol:.0f}%)")

    if news_signal:
        news_score = news_signal.get("news_score", 0)
        if news_score >= 20:
            score += 20
            reasons.append(f"News positives ({news_signal.get('positive')} articles)")
        elif news_score <= -20:
            score -= 25
            reasons.append(f"News negatives ({news_signal.get('negative')} articles)")
        elif news_score > 0:
            score += 10
            reasons.append("News globalement positives")

    if intelligence_signal:
        buzz_score = intelligence_signal.get("buzz_score", 0)
        if buzz_score > 50:
            score += 25
            reasons.append(f"Buzz social fort ({buzz_score}/100)")
        elif buzz_score > 20:
            score += 10
            reasons.append(f"Buzz social modere ({buzz_score}/100)")

    # Apprentissage — ajustement basé sur l'historique du coin
    learning_adj = get_coin_learning_adjustment(coin)
    if learning_adj != 0:
        score += learning_adj
        if learning_adj < 0:
            reasons.append(f"Historique negatif sur {coin} ({learning_adj:+d})")
        else:
            reasons.append(f"Historique positif sur {coin} ({learning_adj:+d})")

    score = max(0, min(100, score))

    # Seuil relevé à 65 pour éviter les faux signaux
    recommendation = "hold"
    if score >= 65:
        recommendation = "buy"
    elif score <= 20:
        recommendation = "sell"

    return {
        "coin": coin,
        "final_score": score,
        "recommendation": recommendation,
        "reasons": " | ".join(r for r in reasons if r)
    }

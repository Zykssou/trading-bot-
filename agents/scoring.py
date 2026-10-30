def calculate_score(scanner_signal, intelligence_signal=None, history_signal=None, news_signal=None):
    score = scanner_signal.get("score", 0)
    reasons = [scanner_signal.get("reason", "")]

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

        # RSI
        if rsi_val is not None:
            if rsi_val < 30:
                score += 30
                reasons.append(f"RSI survente ({rsi_val:.0f})")
            elif rsi_val < 45:
                score += 10
                reasons.append(f"RSI neutre bas ({rsi_val:.0f})")
            elif rsi_val > 70:
                score -= 30
                reasons.append(f"RSI surachat ({rsi_val:.0f})")
            elif rsi_val > 60:
                score -= 10
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

    score = max(0, min(100, score))
    recommendation = "hold"
    if score >= 50:
        recommendation = "buy"
    elif score <= 20:
        recommendation = "sell"

    return {
        "coin": scanner_signal.get("coin"),
        "final_score": score,
        "recommendation": recommendation,
        "reasons": " | ".join(r for r in reasons if r)
    }

def calculate_score(scanner_signal, intelligence_signal=None, history_signal=None):
    score = scanner_signal.get("score", 0)
    reasons = [scanner_signal.get("reason", "")]

    if history_signal:
        rsi_val = history_signal.get("rsi")
        trend = history_signal.get("trend")
        macd_val = history_signal.get("macd")

        if trend == "haussier":
            score += 20
            reasons.append("Tendance 30j haussiere")
        else:
            score -= 20
            reasons.append("Tendance 30j baissiere")

        if rsi_val is not None:
            if rsi_val < 30:
                score += 30
                reasons.append(f"RSI survente ({rsi_val:.0f})")
            elif rsi_val > 70:
                score -= 30
                reasons.append(f"RSI surachat ({rsi_val:.0f})")

        if macd_val is not None:
            if macd_val > 0:
                score += 15
                reasons.append("MACD positif")
            else:
                score -= 10
                reasons.append("MACD negatif")

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

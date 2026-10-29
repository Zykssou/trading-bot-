def calculate_score(scanner_signal, intelligence_signal=None):
    score = scanner_signal.get("score", 0)
    reasons = [scanner_signal.get("reason", "")]

    # Bonus si intelligence sociale confirme
    if intelligence_signal:
        buzz_score = intelligence_signal.get("buzz_score", 0)
        if buzz_score > 50:
            score += 25
            reasons.append(f"Buzz social fort ({buzz_score}/100)")
        elif buzz_score > 20:
            score += 10
            reasons.append(f"Buzz social modéré ({buzz_score}/100)")

    # Normalise entre 0 et 100
    score = max(0, min(100, score))

    recommendation = "hold"
    if score >= 30:
        recommendation = "buy"
    elif score <= 10:
        recommendation = "sell"

    return {
        "coin": scanner_signal.get("coin"),
        "final_score": score,
        "recommendation": recommendation,
        "reasons": " | ".join(r for r in reasons if r)
    }

def classify_intent(query: str) -> str:
    q = query.lower()

    if "authorization" in q or "auth" in q:
        return "AUTH_TRENDS"

    if "settlement" in q or "clearing" in q:
        return "SETTLEMENT_ANALYSIS"

    if "performance" in q or "network" in q:
        return "PERFORMANCE_REPORT"

    if "recommend" in q or "optimiz" in q or "action" in q:
        return "OPTIMIZATION_RECOMMENDATION"

    return "GENERAL"

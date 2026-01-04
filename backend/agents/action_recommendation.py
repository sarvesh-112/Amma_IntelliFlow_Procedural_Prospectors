def recommend_actions(explanation, anomalies=None):
    """
    Generate business actions based on root cause explanation.
    """

    actions = []
    text = explanation.lower()

    if "decline" in text:
        actions.append({
            "action": "Review authorization rules and retry logic",
            "impact": "Increase approval rates and transaction throughput",
            "priority": "High",
            "owner": "Authorization Operations",
            "confidence": "0.85"
        })

    if "settlement" in text or "delay" in text:
        actions.append({
            "action": "Optimize settlement batching and regional clearing schedules",
            "impact": "Reduce settlement delays and reconciliation issues",
            "priority": "Medium",
            "owner": "Settlement Operations",
            "confidence": "0.75"
        })

    if not actions:
        actions.append({
            "action": "Continue monitoring network metrics",
            "impact": "No immediate operational risk detected",
            "priority": "Low",
            "owner": "Network Monitoring",
            "confidence": "0.60"
        })

    return actions

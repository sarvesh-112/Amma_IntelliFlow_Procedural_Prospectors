def detect_anomalies(summary):
    anomalies = []

    key_metrics = summary.get("key_metrics", {})

    if "declined_txns" in key_metrics:
        mean_decline = key_metrics["declined_txns"].get("mean", 0)
        if mean_decline > 500:
            anomalies.append({
                "type": "AUTH_DECLINE_SPIKE",
                "severity": "high",
                "metric": "declined_txns",
                "message": f"High average authorization declines detected ({mean_decline:.0f})"
            })

    if "delay_hours" in key_metrics:
        mean_delay = key_metrics["delay_hours"].get("mean", 0)
        if mean_delay > 5:
            anomalies.append({
                "type": "SETTLEMENT_DELAY",
                "severity": "medium",
                "metric": "delay_hours",
                "message": f"Settlement delays unusually high (avg {mean_delay:.1f} hrs)"
            })

    if not anomalies:
        anomalies.append({
            "type": "NO_ANOMALY",
            "severity": "low",
            "message": "No significant anomalies detected"
        })

    return anomalies

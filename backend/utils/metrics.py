def compute_mean_metric(summaries, metric_name):
    """
    Compute average of a numeric metric across multiple report summaries.
    """
    values = []

    for s in summaries:
        metrics = s.get("key_metrics", {})
        if metric_name in metrics:
            values.append(metrics[metric_name].get("mean", 0))

    if not values:
        return 0

    return round(sum(values) / len(values), 2)


def extract_trend(summaries, metric_name):
    """
    Return a simple trend list for charting.
    """
    trend = []

    for idx, s in enumerate(summaries):
        metrics = s.get("key_metrics", {})
        value = metrics.get(metric_name, {}).get("mean", 0)
        trend.append({
            "index": idx + 1,
            "value": value
        })

    return trend

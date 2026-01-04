import pandas as pd


def understand_report(path):
    df = pd.read_csv(path)

    summary = {
        "report_type": infer_report_type(path, df),
        "rows": len(df),
        "columns": list(df.columns),
        "key_metrics": extract_key_metrics(df),
        "sample_rows": df.head(3).to_dict(orient="records"),
        "text_summary": generate_text_summary(path, df)
    }

    return summary


def infer_report_type(path, df):
    path_lower = path.lower()
    if "auth" in path_lower:
        return "authorization"
    if "settlement" in path_lower:
        return "settlement"
    return "unknown"


def extract_key_metrics(df):
    metrics = {}

    for col in df.columns:
        if df[col].dtype in ["int64", "float64"]:
            metrics[col] = {
                "mean": float(df[col].mean()),
                "min": float(df[col].min()),
                "max": float(df[col].max())
            }

    return metrics


def generate_text_summary(path, df):
    summary_lines = [
        f"Report file: {path}",
        f"Total rows: {len(df)}",
        f"Columns: {', '.join(df.columns)}"
    ]

    for col in df.columns:
        if df[col].dtype in ["int64", "float64"]:
            summary_lines.append(
                f"{col} ranges from {df[col].min()} to {df[col].max()} with an average of {df[col].mean():.2f}"
            )

    return " | ".join(summary_lines)

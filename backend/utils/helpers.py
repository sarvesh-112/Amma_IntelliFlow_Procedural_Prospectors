def safe_lower(text):
    """
    Safely lowercase text.
    """
    if not text:
        return ""
    return str(text).lower()


def truncate_text(text, max_length=500):
    """
    Truncate long text for UI or embedding safety.
    """
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def is_numeric(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False

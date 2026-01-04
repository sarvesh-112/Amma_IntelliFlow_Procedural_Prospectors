import time
from datetime import datetime

# In-memory agent execution log (demo-safe)
_AGENT_LOGS = []


def log_agent_step(
    agent_name: str,
    input_data=None,
    output_data=None,
    metadata: dict = None
):
    """
    Log a single agent execution step.

    Args:
        agent_name (str): Name of the agent
        input_data (any): Input given to the agent
        output_data (any): Output produced by the agent
        metadata (dict): Optional extra info (intent, severity, etc.)
    """

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent_name,
        "input": _safe_stringify(input_data),
        "output": _safe_stringify(output_data),
        "metadata": metadata or {}
    }

    _AGENT_LOGS.append(log_entry)


def get_agent_logs(limit: int = 50):
    """
    Retrieve recent agent logs (most recent last).
    """
    return _AGENT_LOGS[-limit:]


def clear_agent_logs():
    """
    Clear all logs (useful between demos).
    """
    _AGENT_LOGS.clear()


# -------------------- HELPERS --------------------

def _safe_stringify(obj):
    """
    Convert objects to readable strings without crashing.
    """
    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    try:
        return str(obj)
    except Exception:
        return "<unserializable>"

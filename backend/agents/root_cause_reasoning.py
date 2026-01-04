import os
from openai import OpenAI


def explain_root_cause(query, context, intent):
    """
    Intent-aware GenAI reasoning for Visa payment intelligence.
    Falls back to deterministic logic if LLM unavailable.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    # -------- SAFE FALLBACK IF NO KEY --------
    if not api_key:
        return fallback_reasoning(intent, context)

    try:
        client = OpenAI(api_key=api_key)

        prompt = f"""
You are an autonomous Visa payment network intelligence agent.

User Intent:
{intent}

Context (retrieved from authorization and/or settlement reports):
{context}

Instructions:
- Respond strictly according to the intent
- Use Visa network terminology
- Be concise, operational, and decision-focused

Intent-specific guidance:
- AUTH_TRENDS → issuer behavior, approval rates, decline patterns
- SETTLEMENT_ANALYSIS → clearing, settlement latency, reconciliation
- PERFORMANCE_REPORT → end-to-end network health and throughput
- OPTIMIZATION_RECOMMENDATION → concrete operational actions only

Respond in clear business language.
"""

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            temperature=0.2
        )

        # ✅ Safe extraction (prevents crashes)
        if hasattr(response, "output_text") and response.output_text:
            return response.output_text

        return fallback_reasoning(intent, context)

    except Exception:
        # -------- ABSOLUTE DEMO SAFETY --------
        return fallback_reasoning(intent, context)


# -------------------- FALLBACK LOGIC --------------------

def fallback_reasoning(intent, context):
    """
    Deterministic, intent-based fallback reasoning.
    Ensures query-sensitive behavior even without LLM.
    """

    c = context.lower()

    if intent == "AUTH_TRENDS":
        if "decline" in c:
            return (
                "Authorization approval rates have deteriorated due to issuer-side "
                "risk tightening, resulting in elevated decline volumes across the network."
            )
        return (
            "Authorization behavior remains stable, with no material deviation "
            "in issuer approval patterns."
        )

    if intent == "SETTLEMENT_ANALYSIS":
        if "delay" in c:
            return (
                "Settlement delays are observed despite stable authorization volumes, "
                "indicating bottlenecks in clearing or regional settlement windows."
            )
        return (
            "Settlement processing remains within expected thresholds with no "
            "significant downstream latency detected."
        )

    if intent == "PERFORMANCE_REPORT":
        return (
            "Overall network performance reflects upstream authorization variability "
            "cascading into downstream settlement efficiency and throughput."
        )

    if intent == "OPTIMIZATION_RECOMMENDATION":
        return (
            "Optimizing issuer retry logic and aligning regional settlement batching "
            "windows can stabilize throughput and reduce processing latency."
        )

    # -------- GENERAL FALLBACK --------
    return (
        "Payment network behavior indicates upstream authorization dynamics influencing "
        "downstream settlement performance."
    )

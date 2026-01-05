"""
Decision Confidence Guardrail Agent
-----------------------------------
Estimates confidence and risk for AI-driven payment decisions.

Purpose:
• Prevent overconfident automation
• Signal when human review is needed
• Align with enterprise risk governance (Visa-grade)
• Provide explainable confidence scoring for audit trails
"""

from typing import Dict, List, Optional
from datetime import datetime


def assess_decision_confidence(
    intent: str,
    root_cause: str,
    anomalies: Optional[List[dict]] = None,
    counterfactual: Optional[Dict] = None,
    historical_accuracy: Optional[float] = None
) -> Dict:
    """
    Multi-factor confidence assessment for payment intelligence decisions.
    
    Args:
        intent: Classified user intent (AUTH_TRENDS, SETTLEMENT_ANALYSIS, etc.)
        root_cause: Root cause analysis text
        anomalies: List of detected anomalies
        counterfactual: Counterfactual simulation result
        historical_accuracy: Past accuracy rate for similar decisions (0.0-1.0)
    
    Returns:
        dict: Confidence assessment with score, level, escalation flag, and rationale
    """
    
    anomalies = anomalies or []
    score = 0.0
    reasons = []
    risk_flags = []
    
    # -----------------------------
    # 1. Intent Stability (0-30 points)
    # -----------------------------
    INTENT_CONFIDENCE = {
        "AUTH_TRENDS": 0.30,
        "SETTLEMENT_ANALYSIS": 0.30,
        "PERFORMANCE_REPORT": 0.25,
        "OPTIMIZATION_RECOMMENDATION": 0.20,
        "FRAUD_DETECTION": 0.28,
        "NETWORK_HEALTH": 0.27
    }
    
    intent_score = INTENT_CONFIDENCE.get(intent, 0.15)
    score += intent_score
    
    if intent_score >= 0.28:
        reasons.append(f"High-confidence intent: {intent} (well-established pattern)")
    elif intent_score >= 0.20:
        reasons.append(f"Moderate-confidence intent: {intent} (requires validation)")
    else:
        reasons.append(f"Low-confidence intent: {intent} (novel or uncertain pattern)")
        risk_flags.append("Unfamiliar intent pattern")
    
    # -----------------------------
    # 2. Anomaly Signal Strength (0-25 points)
    # -----------------------------
    if len(anomalies) >= 3:
        score += 0.25
        reasons.append(f"Strong anomaly detection: {len(anomalies)} signals identified")
    elif len(anomalies) >= 1:
        score += 0.18
        reasons.append(f"Moderate anomaly detection: {len(anomalies)} signals identified")
    else:
        score += 0.08
        reasons.append("Weak anomaly signals: diagnosis based on aggregate patterns")
        risk_flags.append("Limited anomaly evidence")
    
    # Check for high-severity anomalies
    high_severity_count = sum(1 for a in anomalies if a.get('severity') == 'HIGH')
    if high_severity_count > 0:
        score += 0.05
        reasons.append(f"High-severity anomalies detected ({high_severity_count})")
    
    # -----------------------------
    # 3. Root Cause Analysis Depth (0-20 points)
    # -----------------------------
    rc_lower = (root_cause or "").lower()
    rc_length = len(root_cause or "")
    
    # Check for specific keywords indicating detailed analysis
    detailed_keywords = ["issuer", "clearing", "batch", "threshold", "regional", "velocity"]
    keyword_matches = sum(1 for kw in detailed_keywords if kw in rc_lower)
    
    if rc_length > 200 and keyword_matches >= 3:
        score += 0.20
        reasons.append("Comprehensive root cause analysis with specific operational details")
    elif rc_length > 100 and keyword_matches >= 2:
        score += 0.15
        reasons.append("Moderate root cause analysis depth")
    else:
        score += 0.08
        reasons.append("Limited root cause analysis detail")
        risk_flags.append("Shallow causal reasoning")
    
    # -----------------------------
    # 4. Counterfactual Validation (0-15 points)
    # -----------------------------
    if counterfactual:
        cf_confidence = counterfactual.get('confidence', 'Low')
        
        if cf_confidence in ['High', 'Medium-High']:
            score += 0.15
            reasons.append("High-confidence counterfactual simulation validates recommendation")
        elif cf_confidence == 'Medium':
            score += 0.12
            reasons.append("Moderate counterfactual simulation support")
        else:
            score += 0.08
            reasons.append("Low-confidence counterfactual simulation")
            risk_flags.append("Weak counterfactual support")
    else:
        score += 0.05
        reasons.append("No counterfactual simulation available")
        risk_flags.append("Missing what-if analysis")
    
    # -----------------------------
    # 5. Historical Accuracy Track Record (0-10 points)
    # -----------------------------
    if historical_accuracy is not None:
        if historical_accuracy >= 0.85:
            score += 0.10
            reasons.append(f"Strong historical accuracy: {historical_accuracy:.1%}")
        elif historical_accuracy >= 0.70:
            score += 0.07
            reasons.append(f"Moderate historical accuracy: {historical_accuracy:.1%}")
        else:
            score += 0.03
            reasons.append(f"Weak historical accuracy: {historical_accuracy:.1%}")
            risk_flags.append("Low past prediction accuracy")
    
    # -----------------------------
    # Normalize score (0.0 - 1.0)
    # -----------------------------
    score = min(score, 1.0)
    
    # -----------------------------
    # Classification & Escalation Logic
    # -----------------------------
    if score >= 0.80:
        level = "HIGH"
        escalation = False
        recommendation = "Suitable for automated execution with monitoring"
    elif score >= 0.65:
        level = "MEDIUM-HIGH"
        escalation = False
        recommendation = "Proceed with enhanced monitoring and post-execution review"
    elif score >= 0.50:
        level = "MEDIUM"
        escalation = True
        recommendation = "Human review recommended before execution"
    elif score >= 0.35:
        level = "MEDIUM-LOW"
        escalation = True
        recommendation = "Human approval required - insufficient confidence for automation"
    else:
        level = "LOW"
        escalation = True
        recommendation = "Manual investigation required - do not automate"
    
    # -----------------------------
    # Risk Assessment
    # -----------------------------
    if len(risk_flags) >= 3:
        risk_level = "HIGH"
    elif len(risk_flags) >= 2:
        risk_level = "MEDIUM"
    elif len(risk_flags) >= 1:
        risk_level = "LOW"
    else:
        risk_level = "MINIMAL"
    
    return {
        "confidence_score": round(score, 3),
        "confidence_level": level,
        "human_review_required": escalation,
        "recommendation": recommendation,
        "risk_level": risk_level,
        "risk_flags": risk_flags,
        "rationale": reasons,
        "decision_metadata": {
            "intent": intent,
            "anomaly_count": len(anomalies),
            "high_severity_anomalies": high_severity_count if anomalies else 0,
            "counterfactual_available": counterfactual is not None,
            "assessed_at": datetime.utcnow().isoformat()
        }
    }


def format_confidence_report(assessment: Dict) -> str:
    """
    Generate human-readable confidence report for dashboard display.
    
    Args:
        assessment: Output from assess_decision_confidence()
    
    Returns:
        str: Formatted confidence report
    """
    
    report = f"""
🛡️ Decision Confidence Assessment

Confidence Score: {assessment['confidence_score']:.1%} ({assessment['confidence_level']})
Risk Level: {assessment['risk_level']}
Human Review: {"✅ REQUIRED" if assessment['human_review_required'] else "❌ NOT REQUIRED"}

📋 Recommendation:
{assessment['recommendation']}

🔍 Analysis Rationale:
"""
    
    for i, reason in enumerate(assessment['rationale'], 1):
        report += f"\n  {i}. {reason}"
    
    if assessment['risk_flags']:
        report += "\n\n⚠️ Risk Flags:"
        for flag in assessment['risk_flags']:
            report += f"\n  • {flag}"
    
    return report
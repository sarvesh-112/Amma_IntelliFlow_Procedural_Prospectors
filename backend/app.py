from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os

# -------- AGENTS --------
from agents.report_understanding import understand_report
from agents.anomaly_detection import detect_anomalies
from agents.intent_classifier import classify_intent
from agents.root_cause_reasoning import explain_root_cause
from agents.action_recommendation import recommend_actions

# -------- RAG --------
from rag.embed import embed_texts
from rag.retrieve import retrieve_context

# -------- AGENT LOGGER --------
from agents.agent_logger import (
    log_agent_step,
    get_agent_logs,
    clear_agent_logs   # ✅ ADD THIS
)

# -------------------- APP SETUP --------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "../frontend/templates")
)
CORS(app)

# -------------------- MEMORY --------------------

CACHE = {
    "authorization": [],
    "settlement": []
}

# -------------------- ROUTES --------------------

@app.route("/")
def home():
    return render_template("upload.html")


@app.route("/agents")
def agents_view():
    return render_template("agents.html")


# -------------------- UPLOAD PIPELINE --------------------

@app.route("/upload", methods=["POST"])
def upload():
    report_type = request.form["type"]  # authorization | settlement
    file = request.files["file"]

    save_dir = os.path.join(BASE_DIR, "data", report_type)
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, file.filename)
    file.save(save_path)

    # -------- Agent 1: Report Understanding --------
    summary = understand_report(save_path)
    log_agent_step(
        agent_name="ReportUnderstandingAgent",
        input_data=file.filename,
        output_data=summary,
        metadata={"report_type": report_type}
    )

    # -------- Agent 2: Anomaly Detection --------
    anomalies = detect_anomalies(summary)
    log_agent_step(
        agent_name="AnomalyDetectionAgent",
        input_data=summary.get("key_metrics"),
        output_data=anomalies,
        metadata={"report_type": report_type}
    )

    # Cache summary
    CACHE[report_type].append(summary)

    # -------- RAG: Embedding --------
    embed_texts(
        summary["text_summary"],
        tag=report_type.upper()
    )
    log_agent_step(
        agent_name="RAGEmbeddingAgent",
        input_data=report_type,
        output_data="Embedding stored"
    )

    return jsonify({
        "message": f"{report_type.capitalize()} report processed",
        "anomalies": anomalies
    })


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# -------------------- CHAT / REASONING PIPELINE --------------------

@app.route("/chat", methods=["POST"])
def chat():
    query = request.json["query"]

    # -------- Agent 0: Intent Classification --------
    intent = classify_intent(query)
    log_agent_step(
        agent_name="IntentClassificationAgent",
        input_data=query,
        output_data=intent
    )

    # -------- RAG: Retrieval --------
    context = retrieve_context(f"{intent}: {query}")
    log_agent_step(
        agent_name="RAGRetrievalAgent",
        input_data=intent,
        output_data=context
    )

    # -------- Agent 3: Root Cause Reasoning --------
    explanation = explain_root_cause(query, context, intent)
    log_agent_step(
        agent_name="RootCauseReasoningAgent",
        input_data={"intent": intent, "query": query},
        output_data=explanation
    )

    # -------- Agent 4: Action Recommendation --------
    actions = recommend_actions(explanation)
    log_agent_step(
        agent_name="ActionRecommendationAgent",
        input_data=explanation,
        output_data=actions
    )

    return jsonify({
        "intent": intent,
        "analysis": explanation,
        "actions": actions
    })


# -------------------- AGENT LOGS API --------------------

@app.route("/agent-logs", methods=["GET"])
def agent_logs_api():
    """
    Exposes agent execution logs for visualization.
    """
    return jsonify(get_agent_logs())


@app.route("/clear-logs", methods=["POST"])
def clear_logs_api():
    """
    Clears all agent execution logs.
    """
    clear_agent_logs()
    return jsonify({
        "status": "success",
        "message": "Agent logs cleared"
    })


# -------------------- CHART DATA API --------------------

@app.route("/chart-data", methods=["GET"])
def chart_data():
    auth_declines = []
    settlement_delays = []

    for s in CACHE["authorization"]:
        metrics = s.get("key_metrics", {})
        if "declined_txns" in metrics:
            auth_declines.append(metrics["declined_txns"].get("mean", 0))

    for s in CACHE["settlement"]:
        metrics = s.get("key_metrics", {})
        if "delay_hours" in metrics:
            settlement_delays.append(metrics["delay_hours"].get("mean", 0))

    return jsonify({
        "authorization": {
            "avg_declines": round(sum(auth_declines) / len(auth_declines), 2)
            if auth_declines else 0
        },
        "settlement": {
            "avg_delay_hours": round(sum(settlement_delays) / len(settlement_delays), 2)
            if settlement_delays else 0
        }
    })


# -------------------- MAIN --------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT
    app.run(
        host="0.0.0.0",  # REQUIRED for Render
        port=port,
        debug=True
    )


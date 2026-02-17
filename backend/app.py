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
from agents.counterfactual_simulation import simulate_counterfactual
from agents.decision_confidence import assess_decision_confidence

# -------- RAG --------
from rag.embed import embed_texts
from rag.retrieve import retrieve_context

# -------- AGENT LOGGER --------
from agents.agent_logger import (
    log_agent_step,
    get_agent_logs,
    clear_agent_logs
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


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/agents")
def agents_view():
    return render_template("agents.html")


# -------------------- UPLOAD PIPELINE --------------------

@app.route("/upload", methods=["POST"])
def upload():
    try:
        # Handle client disconnect gracefully
        try:
            form_data = request.form
            files_data = request.files
        except Exception as e:
            print(f"⚠️ Error reading request data: {str(e)}")
            return jsonify({
                "error": "Upload interrupted. Please try again with a smaller file or check your connection."
            }), 400
        
        # ✅ FIX 1: Validate report type
        if 'type' not in form_data:
            return jsonify({
                "error": "Report type is required"
            }), 400
        
        report_type = form_data["type"]
        
        # Validate report type value
        if report_type not in ["authorization", "settlement"]:
            return jsonify({
                "error": f"Invalid report type: {report_type}. Must be 'authorization' or 'settlement'"
            }), 400
        
        # ✅ FIX 2: Validate file upload
        if 'file' not in files_data:
            return jsonify({
                "error": "No file uploaded"
            }), 400
        
        file = files_data["file"]
        
        if file.filename == '':
            return jsonify({
                "error": "No file selected"
            }), 400
        
        # ✅ FIX 3: Validate CSV file
        if not file.filename.lower().endswith('.csv'):
            return jsonify({
                "error": "Only CSV files are allowed"
            }), 400

        # Create save directory
        save_dir = os.path.join(BASE_DIR, "data", report_type)
        os.makedirs(save_dir, exist_ok=True)

        # ✅ FIX: Use timestamp to ensure unique filename
        import time
        timestamp = int(time.time())
        base_filename = file.filename
        filename_parts = os.path.splitext(base_filename)
        unique_filename = f"{filename_parts[0]}_{timestamp}{filename_parts[1]}"
        save_path = os.path.join(save_dir, unique_filename)
        
        file.save(save_path)
        print(f"✅ File saved: {save_path}")

        # -------- Agent 1: Report Understanding --------
        print(f"🔄 Starting report understanding for {report_type}...")
        try:
            summary = understand_report(save_path)
            
            # 🆕 ENHANCED DEBUG LOGGING
            print(f"📊 Summary returned: {summary}")
            print(f"📊 Summary type: {type(summary)}")
            print(f"📊 Summary keys: {summary.keys() if summary else 'None'}")
            
            if summary and 'key_metrics' in summary:
                print(f"📊 Key Metrics: {summary['key_metrics']}")
                print(f"📊 Key Metrics keys: {summary['key_metrics'].keys()}")
            else:
                print(f"⚠️ WARNING: No 'key_metrics' found in summary!")
            
            log_agent_step(
                agent_name="ReportUnderstandingAgent",
                input_data=file.filename,
                output_data=summary,
                metadata={"report_type": report_type}
            )
            print(f"✅ Report understanding complete")
        except Exception as e:
            print(f"❌ Report understanding failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": f"Failed to understand report: {str(e)}"
            }), 500

        # -------- Agent 2: Anomaly Detection --------
        try:
            anomalies = detect_anomalies(summary)
            log_agent_step(
                agent_name="AnomalyDetectionAgent",
                input_data=summary.get("key_metrics"),
                output_data=anomalies,
                metadata={"report_type": report_type}
            )
            print(f"✅ Anomaly detection complete: {len(anomalies)} anomalies found")
        except Exception as e:
            print(f"❌ Anomaly detection failed: {str(e)}")
            # Continue even if anomaly detection fails
            anomalies = []

        # 🆕 CACHE THE SUMMARY
        CACHE[report_type].append(summary)
        print(f"📦 Cached {report_type} report. Total cached: {len(CACHE[report_type])}")
        print(f"📦 Current CACHE: authorization={len(CACHE['authorization'])}, settlement={len(CACHE['settlement'])}")

        # -------- RAG: Embedding --------
        try:
            embed_texts(summary["text_summary"], tag=report_type.upper())
            log_agent_step(
                agent_name="RAGEmbeddingAgent",
                input_data=report_type,
                output_data="Embedding stored"
            )
            print(f"✅ RAG embedding complete")
        except Exception as e:
            print(f"⚠️ RAG embedding failed (non-critical): {str(e)}")

        return jsonify({
            "message": f"{report_type.capitalize()} report processed successfully",
            "anomalies": anomalies,
            "filename": file.filename,
            "report_type": report_type,
            "cached_count": len(CACHE[report_type])
        }), 200

    except Exception as e:
        print(f"❌ Upload failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Upload failed: {str(e)}"
        }), 500


# -------------------- CHAT / AGENTIC PIPELINE --------------------

@app.route("/chat", methods=["POST"])
def chat():
    try:
        payload = request.json or {}
        query = payload.get("query", "")
        show_counterfactual = payload.get("show_counterfactual", True)

        if not query:
            return jsonify({
                "error": "Query is required"
            }), 400

        # -------- Agent 0: Intent Classification --------
        intent = classify_intent(query)
        log_agent_step("IntentClassificationAgent", query, intent)

        # -------- RAG: Context Retrieval --------
        context = retrieve_context(f"{intent}: {query}")
        log_agent_step("RAGRetrievalAgent", intent, context)

        # -------- Agent 3: Root Cause Reasoning --------
        explanation = explain_root_cause(query, context, intent)
        log_agent_step(
            "RootCauseReasoningAgent",
            {"intent": intent, "query": query},
            explanation
        )

        # -------- Agent 5: Counterfactual Simulation --------
        counterfactual = None
        if show_counterfactual:
            counterfactual = simulate_counterfactual(
                intent=intent,
                root_cause=explanation
            )
            log_agent_step(
                "CounterfactualSimulationAgent",
                {"intent": intent},
                counterfactual
            )

        # -------- Agent 4: Action Recommendation --------
        actions = recommend_actions(explanation)
        log_agent_step(
            "ActionRecommendationAgent",
            explanation,
            actions
        )

        # -------- Agent 6: Decision Confidence Guardrail --------
        confidence = assess_decision_confidence(
            intent=intent,
            root_cause=explanation,
            anomalies=None,
            counterfactual=counterfactual,
            historical_accuracy=None
        )
        log_agent_step(
            "DecisionConfidenceGuardrailAgent",
            {"intent": intent},
            confidence
        )

        # -------- FINAL RESPONSE --------
        response = {
            "intent": intent,
            "analysis": explanation,
            "actions": actions,
            "decision_confidence": confidence
        }

        if counterfactual:
            response["counterfactual"] = counterfactual

        return jsonify(response), 200

    except Exception as e:
        print(f"❌ Chat failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Chat processing failed: {str(e)}"
        }), 500


# -------------------- AGENT LOGS API --------------------

@app.route("/agent-logs", methods=["GET"])
def agent_logs_api():
    return jsonify(get_agent_logs())


@app.route("/clear-logs", methods=["POST"])
def clear_logs_api():
    clear_agent_logs()
    return jsonify({
        "status": "success",
        "message": "Agent logs cleared"
    })


# -------------------- CHART DATA API --------------------

@app.route("/chart-data", methods=["GET"])
def chart_data():
    print("\n" + "="*60)
    print("🔍 CHART DATA ENDPOINT CALLED")
    print("="*60)
    
    auth_declines = []
    settlement_delays = []
    auth_labels = []
    settlement_labels = []

    # 🆕 DEBUG: Show cache contents
    print(f"📦 CACHE Status:")
    print(f"   - Authorization reports: {len(CACHE['authorization'])}")
    print(f"   - Settlement reports: {len(CACHE['settlement'])}")
    
    if CACHE["authorization"]:
        print(f"\n📊 Authorization Cache Contents:")
        for idx, item in enumerate(CACHE["authorization"]):
            print(f"   Report {idx}: {item.keys() if item else 'None'}")
    
    if CACHE["settlement"]:
        print(f"\n📊 Settlement Cache Contents:")
        for idx, item in enumerate(CACHE["settlement"]):
            print(f"   Report {idx}: {item.keys() if item else 'None'}")

    # Extract authorization data from each uploaded report
    print(f"\n🔍 Processing {len(CACHE['authorization'])} authorization report(s)...")
    for idx, s in enumerate(CACHE["authorization"]):
        metrics = s.get("key_metrics", {})
        print(f"\n📊 Auth Report {idx + 1}:")
        print(f"   Available metrics: {list(metrics.keys())}")
        
        # Try multiple possible field names
        decline_value = None
        possible_fields = ["declined_txns", "decline_rate", "declines", "authorization_declines", 
                          "declined_transactions", "decline_count"]
        
        for field in possible_fields:
            if field in metrics:
                if isinstance(metrics[field], dict):
                    decline_value = metrics[field].get("mean", metrics[field].get("value", 0))
                else:
                    decline_value = metrics[field]
                print(f"   ✅ Found '{field}' = {decline_value}")
                break
        
        if decline_value is not None:
            auth_declines.append(float(decline_value))
            auth_labels.append(f"Report {idx + 1}")
            print(f"   ✅ Added to chart: {decline_value}")
        else:
            print(f"   ⚠️ No decline metric found. Available: {list(metrics.keys())}")

    # Extract settlement data from each uploaded report
    print(f"\n🔍 Processing {len(CACHE['settlement'])} settlement report(s)...")
    for idx, s in enumerate(CACHE["settlement"]):
        metrics = s.get("key_metrics", {})
        print(f"\n📊 Settlement Report {idx + 1}:")
        print(f"   Available metrics: {list(metrics.keys())}")
        
        # Try multiple possible field names
        delay_value = None
        possible_fields = ["delay_hours", "settlement_delay", "delay", "processing_delay", 
                          "settlement_time", "delay_time"]
        
        for field in possible_fields:
            if field in metrics:
                if isinstance(metrics[field], dict):
                    delay_value = metrics[field].get("mean", metrics[field].get("value", 0))
                else:
                    delay_value = metrics[field]
                print(f"   ✅ Found '{field}' = {delay_value}")
                break
        
        if delay_value is not None:
            settlement_delays.append(float(delay_value))
            settlement_labels.append(f"Report {idx + 1}")
            print(f"   ✅ Added to chart: {delay_value}")
        else:
            print(f"   ⚠️ No delay metric found. Available: {list(metrics.keys())}")

    # 🆕 FALLBACK: Add test data if no real data found
    if len(auth_declines) == 0 and len(CACHE["authorization"]) == 0:
        print("\n⚠️ No authorization data found - using test data")
        auth_declines = [10, 12, 15, 11, 13]
        auth_labels = ["Sample 1", "Sample 2", "Sample 3", "Sample 4", "Sample 5"]
    
    if len(settlement_delays) == 0 and len(CACHE["settlement"]) == 0:
        print("\n⚠️ No settlement data found - using test data")
        settlement_delays = [1.5, 1.8, 2.0, 1.6, 1.9]
        settlement_labels = ["Sample 1", "Sample 2", "Sample 3", "Sample 4", "Sample 5"]

    print(f"\n📊 Final Data for Charts:")
    print(f"   Auth declines: {auth_declines}")
    print(f"   Auth labels: {auth_labels}")
    print(f"   Settlement delays: {settlement_delays}")
    print(f"   Settlement labels: {settlement_labels}")

    # Calculate averages and thresholds
    auth_avg = round(sum(auth_declines) / len(auth_declines), 2) if auth_declines else 0
    settlement_avg = round(sum(settlement_delays) / len(settlement_delays), 2) if settlement_delays else 0
    
    auth_threshold = round(auth_avg * 1.2, 2) if auth_avg > 0 else 15
    settlement_threshold = round(settlement_avg * 1.25, 2) if settlement_avg > 0 else 2.5

    response_data = {
        "authorization": {
            "avg_declines": auth_avg,
            "threshold": auth_threshold,
            "data_points": auth_declines,
            "labels": auth_labels,
            "has_data": len(auth_declines) > 0
        },
        "settlement": {
            "avg_delay_hours": settlement_avg,
            "threshold": settlement_threshold,
            "data_points": settlement_delays,
            "labels": settlement_labels,
            "has_data": len(settlement_delays) > 0
        }
    }
    
    print(f"\n✅ Returning response:")
    print(f"   Authorization has_data: {response_data['authorization']['has_data']}")
    print(f"   Settlement has_data: {response_data['settlement']['has_data']}")
    print("="*60 + "\n")
    
    return jsonify(response_data)


# -------------------- DEBUG ENDPOINT --------------------

@app.route("/debug/cache", methods=["GET"])
def debug_cache():
    """Debug endpoint to inspect cache contents"""
    return jsonify({
        "cache_status": {
            "authorization_count": len(CACHE["authorization"]),
            "settlement_count": len(CACHE["settlement"])
        },
        "authorization_reports": [
            {
                "index": idx,
                "keys": list(report.keys()),
                "key_metrics": list(report.get("key_metrics", {}).keys()) if report.get("key_metrics") else []
            }
            for idx, report in enumerate(CACHE["authorization"])
        ],
        "settlement_reports": [
            {
                "index": idx,
                "keys": list(report.keys()),
                "key_metrics": list(report.get("key_metrics", {}).keys()) if report.get("key_metrics") else []
            }
            for idx, report in enumerate(CACHE["settlement"])
        ]
    })


# -------------------- MAIN --------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Visa Payment Intelligence Platform on port {port}")
    print(f"📁 Base directory: {BASE_DIR}")
    print(f"🔍 Debug endpoint available at: http://localhost:{port}/debug/cache")
    
    # Increase max content length to handle larger files (50MB)
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
"""
Rasa-Compatible REST API Server for Quotes Recommendation Chatbot
Supports standard endpoints:
  - POST /webhooks/rest/webhook (standard Rasa REST channel)
  - POST /model/parse (standard Rasa NLU parse endpoint)
  - GET  /health (health check)
  - GET  /api/quotes (list and filter quotes)
  - GET  / (serves frontend web interface)
"""

import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from nlp_engine import NLPEngine

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(CURRENT_DIR, "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

# Initialize NLP Engine
nlp = NLPEngine()

@app.route("/webhooks/rest/webhook", methods=["POST"])
def rest_webhook():
    """Standard Rasa REST channel webhook."""
    data = request.get_json(force=True, silent=True) or {}
    sender = data.get("sender", "default_user")
    message = data.get("message", "")

    if not message.strip():
        return jsonify([])

    responses = nlp.process_message(sender_id=sender, message=message)
    return jsonify(responses)

@app.route("/model/parse", methods=["POST"])
def model_parse():
    """Standard Rasa NLU endpoint to parse text for intent and entities."""
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "")
    parse_result = nlp.parse_nlu(text)
    return jsonify(parse_result)

@app.route("/health", methods=["GET"])
@app.route("/status", methods=["GET"])
def health_check():
    """Service health and metadata."""
    return jsonify({
        "status": "ok",
        "service": "Quotes Recommendation Chatbot NLP Server",
        "protocol": "Rasa REST API v3.x compatible",
        "total_quotes": len(nlp.quotes),
        "supported_categories": ["Motivation", "Inspiration", "Success", "Love", "Humor"],
        "supported_emotions": ["sad", "stressed", "anxious", "unmotivated", "heartbroken", "happy", "ambitious"]
    })

@app.route("/api/quotes", methods=["GET"])
def get_quotes():
    """Retrieve quotes with optional category or mood filters."""
    category = request.args.get("category")
    mood = request.args.get("mood")
    filtered = nlp.quotes

    if category:
        filtered = [q for q in filtered if q.get("category", "").lower() == category.lower()]
    if mood:
        filtered = [q for q in filtered if mood.lower() in [m.lower() for m in q.get("moods", [])]]

    return jsonify({"count": len(filtered), "quotes": filtered})

@app.route("/api/categories", methods=["GET"])
def get_categories():
    """List categories with quote counts."""
    categories = {}
    for q in nlp.quotes:
        cat = q.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1
    return jsonify(categories)

# Serve Frontend static assets
@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_frontend(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    print(f">> Quotes Recommendation Chatbot REST API running on http://127.0.0.1:{port}")
    print(f">> Webhook: http://127.0.0.1:{port}/webhooks/rest/webhook")
    print(f">> NLU Parse: http://127.0.0.1:{port}/model/parse")
    print(f">> Web Interface: http://127.0.0.1:{port}/")
    app.run(host="0.0.0.0", port=port, debug=False)

"""
app.py
Flask backend for Taxation. Owns the tax engine, relief catalogue and chat,
and serves the single-page frontend.

Run:
    pip install -r requirements.txt
    python app.py
    open http://localhost:5000
"""

import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from calculator import SAMPLE, run_calculation, build_actions
from reliefs import QUESTIONS, RELIEF_CATALOG
from chat import respond

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Serve index.html as a raw file (not through Jinja, so JSX braces are untouched).
app = Flask(__name__, static_folder=TEMPLATES_DIR, static_url_path="")
CORS(app)


@app.route("/")
def index():
    return send_from_directory(TEMPLATES_DIR, "index.html")


@app.get("/api/config")
def config():
    """Static config the frontend renders: wizard questions + relief metadata."""
    return jsonify({
        "ya": 2025,
        "questions": QUESTIONS,
        "reliefs": [{"id": r["id"], "name": r["name"], "cap": r["cap"], "cite": r["cite"]}
                    for r in RELIEF_CATALOG],
    })


@app.get("/api/sample/<mode>")
def sample(mode):
    data = SAMPLE.get(mode)
    if not data:
        return jsonify({"error": "unknown mode"}), 404
    return jsonify(data)


@app.post("/api/calculate")
def calculate():
    body = request.get_json(force=True) or {}
    extracted = body.get("extracted") or {}
    answers = body.get("answers") or {}
    calc = run_calculation(extracted, answers)
    actions = build_actions(extracted, answers, calc)
    return jsonify({"calc": calc, "actions": actions})


@app.post("/api/chat")
def chat():
    body = request.get_json(force=True) or {}
    question = body.get("question", "")
    lang = body.get("lang", "en")
    return jsonify(respond(question, lang))


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

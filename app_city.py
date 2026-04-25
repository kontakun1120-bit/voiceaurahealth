from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime

app = Flask(__name__)

DATA_PATH = "data/sessions.json"


def load_sessions():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_session(session):
    os.makedirs("data", exist_ok=True)
    sessions = load_sessions()
    sessions.append(session)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/room")
def room():
    return render_template("room.html")


@app.route("/health")
def health():
    return render_template("health.html")


@app.route("/lab")
def lab():
    return render_template("lab.html")


@app.route("/team")
def team():
    return render_template("team.html")


@app.route("/api/sessions", methods=["GET"])
def api_sessions():
    return jsonify({
        "sessions": load_sessions()
    })


@app.route("/api/session", methods=["POST"])
def api_save_session():
    data = request.get_json() or {}

    session = {
        "time": datetime.now().isoformat(),
        "energy": data.get("energy", 60),
        "stress": data.get("stress", 40),
        "emotion": data.get("emotion", 55),
        "focus": data.get("focus", 50),
        "social": data.get("social", 50),
        "source": data.get("source", "city"),
        "note": data.get("note", "")
    }

    save_session(session)

    return jsonify({
        "ok": True,
        "session": session
    })


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os

from mini_app.voice_state_engine import VoiceStateEngine

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

CORS(app)

engine = VoiceStateEngine()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WAV_PATH = os.path.join(BASE_DIR, "static", "voice_web.wav")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file"})

        file = request.files["audio"]
        file.save(WAV_PATH)

        result = engine.analyze_from_file(WAV_PATH)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/analyze", methods=["GET"])
def analyze():
    result = engine.analyze_from_file(WAV_PATH)

    return jsonify({
        "stress": result.get("stress", 0),
        "energy": result.get("energy", 0),
        "emotion": result.get("emotion", 0),
        "focus": result.get("focus", 0),
        "social": result.get("social", 0),
        "fatigue": result.get("fatigue", 0),
        "awareness": result.get("awareness", 0)
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

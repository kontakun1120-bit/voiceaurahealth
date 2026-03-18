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
            return jsonify({"error": "No audio"})

        file = request.files["audio"]
        file.save(WAV_PATH)

        result = engine.analyze_from_file(WAV_PATH)

        print("DEBUG RESULT:", result)

        # 🔥 ここ追加
        if result is None:
            result = {}

        # 🔥 キー補完（重要）
        result.setdefault("Stress", 0)
        result.setdefault("Energy", 0)
        result.setdefault("Emotion", 0)
        result.setdefault("Focus", 0)
        result.setdefault("Social", 0)
        result.setdefault("Fatigue", 0)
        result.setdefault("Arousal", 0)

        return jsonify(result)

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)})

@app.route("/analyze", methods=["GET"])
def analyze():
    result = engine.analyze_from_file(WAV_PATH)

    if not result:
        result = {}

    return jsonify({
        "stress": result.get("stress", 0.5),
        "energy": result.get("energy", 0.7),
        "emotion": result.get("emotion", 0.6),
        "focus": result.get("focus", 0.8),
        "social": result.get("social", 0.4),
        "fatigue": result.get("fatigue", 0.3),
        "awareness": result.get("awareness", 0.9)
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
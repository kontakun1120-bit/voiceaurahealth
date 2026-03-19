# ==========================================
# VoiceAura Web App（完全版・安定版）
# ==========================================

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from pydub import AudioSegment

from voice_state_engine import VoiceStateEngine


# ===============================
# Flask設定
# ===============================
app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

CORS(app)

engine = VoiceStateEngine()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WAV_PATH = os.path.join(BASE_DIR, "../static/voice_web.wav")
WEBM_PATH = os.path.join(BASE_DIR, "../static/voice_web.webm")


# ===============================
# ルート
# ===============================
@app.route("/")
def index():
    return render_template("index.html")


# ===============================
# 音声アップロード
# ===============================
@app.route("/upload", methods=["POST"])
def upload():
    try:
        print("=== UPLOAD START ===")

        if "audio" not in request.files:
            print("No audio file")
            return jsonify({"error": "No audio file"})

        file = request.files["audio"]

        # =========================
        # 保存（webm）
        # =========================
        file.save(WEBM_PATH)
        print("Saved WEBM:", WEBM_PATH)

        # =========================
        # webm → wav変換（重要）
        # =========================
        try:
            audio = AudioSegment.from_file(WEBM_PATH)

            # 🔥 安定化（超重要）
            audio = audio.set_sample_width(2)   # 16bit
            audio = audio.set_channels(1)       # mono

            audio.export(WAV_PATH, format="wav")
            print("Converted to WAV:", WAV_PATH)

        except Exception as e:
            print("FFMPEG ERROR:", e)

            return jsonify({
                "Stress": 0,
                "Energy": 0,
                "Emotion": 0,
                "Focus": 0,
                "Social": 0,
                "Fatigue": 0,
                "Arousal": 0,
                "StressComment": "音声変換エラー",
                "Personality": "不明",
                "ColorSector": "不明"
            })

        # =========================
        # 解析
        # =========================
        try:
            result = engine.analyze_from_file(WAV_PATH)
            print("DEBUG RESULT:", result)

        except Exception as e:
            print("ENGINE ERROR:", e)

            return jsonify({
                "Stress": 0,
                "Energy": 0,
                "Emotion": 0,
                "Focus": 0,
                "Social": 0,
                "Fatigue": 0,
                "Arousal": 0,
                "StressComment": "解析エラー",
                "Personality": "不明",
                "ColorSector": "不明"
            })

        # =========================
        # 安全処理
        # =========================
        if result is None:
            result = {}

        print("=== SUCCESS ===")

        return jsonify(result)

    except Exception as e:
        print("FATAL ERROR:", e)

        return jsonify({
            "Stress": 0,
            "Energy": 0,
            "Emotion": 0,
            "Focus": 0,
            "Social": 0,
            "Fatigue": 0,
            "Arousal": 0,
            "StressComment": "致命的エラー",
            "Personality": "不明",
            "ColorSector": "不明"
        })


# ===============================
# health check
# ===============================
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ===============================
# 起動
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
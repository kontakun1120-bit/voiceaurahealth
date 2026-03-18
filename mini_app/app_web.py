# =====================================================
# 1.0.0 import
# =====================================================
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os

from voice_state_engine import VoiceStateEngine


# =====================================================
# 2.0.0 app init
# =====================================================
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

CORS(app)


# =====================================================
# 3.0.0 engine（1回だけ）
# =====================================================
engine = VoiceStateEngine()


# =====================================================
# 4.0.0 path設定
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WAV_PATH = os.path.join(BASE_DIR, "static", "voice_web.wav")


# =====================================================
# 5.0.0 route
# =====================================================
@app.route("/")
def index():
    return render_template("index.html")




# -----------------------------------------------------
# アップロード解析 　（PC、スマホOK）　iPhone駄目?
# -----------------------------------------------------
@app.route("/upload", methods=["POST"])
def upload():

    if "audio" not in request.files:
        return jsonify({"error": "No audio file"})

    file = request.files["audio"]
    file.save(WAV_PATH)

    result = engine.analyze_from_file(WAV_PATH)

    return jsonify(result)


# -----------------------------------------------------
# 録音→解析（本命）
# -----------------------------------------------------
@app.route("/analyze", methods=["POST"])
def analyze():

    try:
        wav_path = record_audio(WAV_PATH)

        result = engine.analyze_from_file(wav_path)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "Stress": 0,
            "Energy": 0,
            "Emotion": 0,
            "Focus": 0,
            "Social": 0,
            "Fatigue": 0,
            "Arousal": 0,
            "StressComment": str(e),
            "Personality": "Error",
            "ColorSector": "None"
        })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# =====================================================
# 6.0.0 録音
# =====================================================
def record_audio(output, sec=5):

    cmd = [
        "ffmpeg",
        "-f", "dshow",
        "-i", 'audio=マイク (TKGOU PnP USB Microphone)',
        "-t", str(sec),
        output,
        "-y"
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output


# =====================================================
# 7.0.0 run
# =====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
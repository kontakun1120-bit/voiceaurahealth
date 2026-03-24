# ==========================================================
# app_web.py（VoiceAuraHealth mini v2）
# ==========================================================

from flask import Flask, render_template, request, jsonify
import os
import uuid

from voice_state_engine import VoiceStateEngine
from pydub import AudioSegment

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

engine = VoiceStateEngine()


# ----------------------------------------------------------
# 0.0 サーバー準備確認
# ----------------------------------------------------------
@app.route("/api/ping")
def ping():
    return "ok"


# ----------------------------------------------------------
# 1.0 index
# ----------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ----------------------------------------------------------
# 2.0 音声アップロードAPI（Railway安定版）
# ----------------------------------------------------------
@app.route("/api/upload", methods=["POST"])
def upload_audio():

    try:
        if "audio" not in request.files:
            return jsonify({"error": "no audio file"}), 400

        file = request.files["audio"]

        if file.filename == "":
            return jsonify({"error": "empty file"}), 400

        # 🔥 Railway対策：/tmp固定
        filename = f"{uuid.uuid4()}.wav"
        path = os.path.join("/tmp", filename)
        file.save(path)

        wav_path = path.replace(".wav", "_conv.wav")

        # 🔥 音声変換
        audio = AudioSegment.from_file(path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(wav_path, format="wav")

        # 🔥 解析
        result = engine.analyze_from_file(wav_path)
        response = format_result(result)

        return jsonify({"result": response})

    except Exception as e:
        print("🔥 ERROR:", e)  # Railwayログ用
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
            if os.path.exists(wav_path):
                os.remove(wav_path)
        except:
            pass


# ----------------------------------------------------------
# 3.0 UI変換ロジック
# ----------------------------------------------------------
def format_result(r):

    scores = {
        "Energy": r["Energy"],
        "Emotion": r["Emotion"],
        "Focus": r["Focus"],
        "Social": r["Social"],
        "Calm": 100 - r["Stress"],
    }

    type_name = r["Personality"]

    color = "#00B7C2"
    if "red" in r["ColorSector"]:
        color = "#FF0000"
    elif "blue" in r["ColorSector"]:
        color = "#0077FF"
    elif "green" in r["ColorSector"]:
        color = "#00A86B"

    score_comments = build_score_comments(scores)
    daily = engine.generate_daily_message()
    summary = engine.generate_empathy_summary(scores)

    return {
        "type": type_name,
        "sector": r["ColorSector"],
        "color": color,
        "scores": scores,
        "score_comments": score_comments,
        "daily_message": daily,
        "summary": summary
    }


# ----------------------------------------------------------
# 3.1 指標ごとのコメント
# ----------------------------------------------------------
def build_score_comments(scores):

    def energy(v):
        if v < 30:
            return "エネルギー低下（疲労傾向）"
        elif v < 60:
            return "エネルギーやや低め"
        else:
            return "エネルギー良好"

    def emotion(v):
        if v < 30:
            return "感情抑制気味"
        elif v < 60:
            return "感情安定"
        else:
            return "感情やや活性"

    def focus(v):
        if v < 30:
            return "集中力低下"
        elif v < 60:
            return "集中やや不安定"
        else:
            return "集中良好"

    def social(v):
        if v < 30:
            return "社交性低下"
        elif v < 60:
            return "やや控えめ"
        else:
            return "社交性良好"

    def calm(v):
        if v < 30:
            return "ストレス高"
        elif v < 60:
            return "ややストレスあり"
        else:
            return "安定状態"

    return {
        "Energy": energy(scores["Energy"]),
        "Emotion": emotion(scores["Emotion"]),
        "Focus": focus(scores["Focus"]),
        "Social": social(scores["Social"]),
        "Calm": calm(scores["Calm"]),
    }


# ----------------------------------------------------------
# 5.0 run
# ----------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
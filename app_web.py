# ==========================================================
# app_web.py（VoiceAuraHealth mini v2）
# ==========================================================

from flask import Flask, render_template, request, jsonify
import os
import uuid

from mini_app.voice_state_engine import VoiceStateEngine
from pydub import AudioSegment

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

engine = VoiceStateEngine()


# ----------------------------------------------------------
# 1.0 index
# ----------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ----------------------------------------------------------
# 2.0 音声アップロードAPI
# ----------------------------------------------------------
@app.route("/api/upload", methods=["POST"])
def upload_audio():

    if "audio" not in request.files:
        return jsonify({"error": "no audio file"})

    file = request.files["audio"]

    filename = f"{uuid.uuid4()}.wav"
    path = os.path.join(UPLOAD_FOLDER, filename)

    file.save(path)



    # 👇ここ追加
    wav_path = path.replace(".wav", "_conv.wav")

    audio = AudioSegment.from_file(path)
    
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

    audio.export(wav_path, format="wav")




    # ----------------------------------------
    # 解析
    # ----------------------------------------
    result = engine.analyze_from_file(wav_path)
#    result = engine.analyze_from_file(path)

    # ----------------------------------------
    # UI用に整形（ここが重要）
    # ----------------------------------------
    response = format_result(result)

    return jsonify({"result": response})


# ----------------------------------------------------------
# 3.0 UI変換ロジック（超重要）
# ----------------------------------------------------------
def format_result(r):

    # UIで使うスコア
    scores = {
        "Energy": r["Energy"],
        "Emotion": r["Emotion"],
        "Focus": r["Focus"],
        "Social": r["Social"],
        "Calm": 100 - r["Stress"],   # ←ここがポイント
    }

    # タイプ
    type_name = r["Personality"]

    # カラー（簡易変換）
    color = "#00B7C2"
    if "red" in r["ColorSector"]:
        color = "#FF0000"
    elif "blue" in r["ColorSector"]:
        color = "#0077FF"
    elif "green" in r["ColorSector"]:
        color = "#00A86B"

    # コメント
    comments = [
        r["StressComment"],
        f"Fatigue: {r['Fatigue']}",
        f"Arousal: {r['Arousal']}"
    ]

    return {
        "type": type_name,
        "sector": r["ColorSector"],
        "color": color,
        "scores": scores,
        "comments": comments
    }


# ----------------------------------------------------------
# 4.0 run
# ----------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
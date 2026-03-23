# ==========================================================
# app_web.py（VoiceAuraHealth mini v2）
# ==========================================================

from flask import Flask, render_template, request, jsonify
import os
import uuid

from mini_app.voice_state_engine import VoiceStateEngine
# from pydub import AudioSegment

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

engine = VoiceStateEngine()


# ----------------------------------------------------------
# 0.0 サーバー準備中→起動 app開始
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
# 2.0 音声アップロードAPI
# ----------------------------------------------------------
@app.route("/api/upload", methods=["POST"])
def upload_audio():

    if "audio" not in request.files:
        return jsonify({"error": "no audio file"})

    file = request.files["audio"]

    if file.filename == "":
        return jsonify({"error": "empty file"})

    filename = f"{uuid.uuid4()}.wav"
    path = os.path.join(UPLOAD_FOLDER, filename)

    file.save(path)



    # 👇ここ追加
    wav_path = path.replace(".wav", "_conv.wav")

    audio = AudioSegment.from_file(path)
    
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

    audio.export(wav_path, format="wav")




    # ----------------------------------------
    # 解析 ファイル削除
    # ----------------------------------------
    try:
        result = engine.analyze_from_file(wav_path)
        response = format_result(result)
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        if os.path.exists(path):
            os.remove(path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

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

    # 院長専用・医療コメント
    score_comments = build_score_comments(scores)
#    comments = build_medical_comments(r)  # 3.1 UI変換ロジック サブdef

    # コメント
#    comments = [
#        r["StressComment"],
#        f"Fatigue: {r['Fatigue']}",
#        f"Arousal: {r['Arousal']}"
#    ]

    return {
        "type": type_name,
        "sector": r["ColorSector"],
        "color": color,
        "scores": scores,
        "score_comments": score_comments
#        "comments": comments
    }

# ----------------------------------------------------------
# 3.1 UI変換ロジック（3.0の医療ロジック変更）
# ----------------------------------------------------------
def build_medical_comments(r):

    comments = []

    stress = r["Stress"]
    fatigue = r["Fatigue"]
    energy = r["Energy"]
    calm = 100 - stress

    # ----------------------------------------
    # ① ストレス判定
    # ----------------------------------------
    if stress > 70:
        comments.append("⚠ 強いストレス状態です")
        comments.append("休養を優先してください")
    elif stress > 50:
        comments.append("ややストレスあり")
    else:
        comments.append("安定状態です")

    # ----------------------------------------
    # ② 疲労
    # ----------------------------------------
    if fatigue > 70:
        comments.append("疲労が蓄積しています")
    elif fatigue > 50:
        comments.append("やや疲労あり")

    # ----------------------------------------
    # ③ エネルギー
    # ----------------------------------------
    if energy < 30:
        comments.append("エネルギー低下")
        comments.append("無理をしないでください")
    elif energy > 70:
        comments.append("活力あり")

    # ----------------------------------------
    # ④ Calm（自律神経）
    # ----------------------------------------
    if calm < 40:
        comments.append("交感神経優位の可能性")
    elif calm > 70:
        comments.append("リラックス状態")

    # ----------------------------------------
    # ⑤ 医療コメント（院長ワード🔥）
    # ----------------------------------------
    if stress > 70 or fatigue > 70:
        comments.append("休養して下さいね。お大事に。")

    return comments

# ----------------------------------------------------------
# 3.1 指標ごとの医療コメント（院長スタイル🔥）
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
# 4.0 run
# ----------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

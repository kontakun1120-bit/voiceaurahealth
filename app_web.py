# ==========================================
# 1.0 VoiceAura Web App（完全版・安定版）
# ==========================================

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from pydub import AudioSegment

from voice_state_engine import VoiceStateEngine

import uuid
import random
from datetime import datetime

# ===============================
# 2.0 Flask設定
# ===============================
##app = Flask(
##    __name__,
##    template_folder="../templates",
#    static_folder="../static"
#)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="../static"
)

CORS(app)

engine = None
# engine = VoiceStateEngine()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WAV_PATH = os.path.join(BASE_DIR, "../static/voice_web.wav")
WEBM_PATH = os.path.join(BASE_DIR, "../static/voice_web.webm")

# ===============================
# 2～3.0 共通関数
# ===============================

# 正規化 （念のため）
def clamp(x):
    return max(0, min(100, x))

# ===============================
# 3.0 ルート
# ===============================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/test")
def test():
    return {"message": "API OK 🚀"}

@app.route("/api/upload", methods=["POST"])
def upload_api():
    file = request.files.get("audio")

    if file is None:
        return {"error": "no file"}

    # =========================
    # 保存
    # =========================

    filename = str(uuid.uuid4()) + ".wav"

    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    # =========================
    # 🔥 VoiceAura接続
    # =========================
    global engine
    if engine is None:
        engine = VoiceStateEngine()

    try:
        result_raw = engine.analyze_from_file(filepath)

    except Exception as e:
        print("ENGINE ERROR:", e)
        return {
            "error": "解析エラー"
        }

    # =========================
    # 🎯 人格タイプ変換（仮ロジック）
    # =========================
    # （ここは後で本格化する）
#    personality = "🔬 Analyst"   # （仮ロジック）
#    color = "#3B82F6"            # （仮ロジック）

    # =========================
    # 🎯 6タイプ分類（完成版）
    # =========================

    if result_raw is None:
        result_raw = {}

    stress = result_raw.get("Stress", 0)
    energy = result_raw.get("Energy", 0)
    emotion = result_raw.get("Emotion", 0)
    focus = result_raw.get("Focus", 0)
    social = result_raw.get("Social", 0)

    stress = clamp(stress)
    energy = clamp(energy)
    emotion = clamp(emotion)
    focus = clamp(focus)
    social = clamp(social)


    # =========================
    # 判定ロジック（仮ロジック）
    # =========================
#    if result_raw:
#        energy = result_raw.get("Energy", 0)#
#
#        if energy > 70:
#            personality = "🔥 Leader"
#            color = "#EF4444"
#        elif energy > 40:
#            personality = "🤝 Empath"
#            color = "#22C55E"
#        else:
#            personality = "🌱 Reflector"
#            color = "#6366F1"

    # =========================
    # 判定ロジック
    # =========================

    # 1️⃣ Leader（行動×外向）
    if energy > 65 and social > 60:
        personality = "🔥 Leader"
        color = "#EF4444"

    # 2️⃣ Empath（感情×共感）
    elif emotion > 65 and social > 55:
        personality = "🤝 Empath"
        color = "#22C55E"

    # 3️⃣ Analyst（集中×思考）
    elif focus > 65:
        personality = "🔬 Analyst"
        color = "#3B82F6"

    # 4️⃣ Reflector（低エネルギー×低刺激）
    elif energy < 40 and stress < 40:
        personality = "🌱 Reflector"
        color = "#6366F1"

    # 5️⃣ Creator（感情×エネルギー）
    elif emotion > 60 and energy > 55:
        personality = "🎨 Creator"
        color = "#EC4899"

    # 6️⃣ Explorer（その他＝バランス型）
    else:
        personality = "🧭 Explorer"
        color = "#F59E0B"

    # =========================
    # 🎨 12セクター分類
    # =========================

    def get_level(value):
        if value > 70:
            return "high"
        else:
            return "low"


    # 各タイプごとに軸を決める
    if "Leader" in personality:
        level = get_level(energy)

        if level == "high":
            color = "#DC2626"  # deep red
            sector = "Leader-High"
        else:
            color = "#F87171"  # light red
            sector = "Leader-Low"

    elif "Empath" in personality:
        level = get_level(emotion)

        if level == "high":
            color = "#16A34A"
            sector = "Empath-High"
        else:
            color = "#86EFAC"
            sector = "Empath-Low"

    elif "Analyst" in personality:
        level = get_level(focus)

        if level == "high":
            color = "#1D4ED8"
            sector = "Analyst-High"
        else:
            color = "#93C5FD"
            sector = "Analyst-Low"

    elif "Reflector" in personality:
        level = get_level(energy)

        if level == "high":
            color = "#4F46E5"
            sector = "Reflector-High"
        else:
            color = "#A5B4FC"
            sector = "Reflector-Low"

    elif "Creator" in personality:
        level = get_level(emotion)

        if level == "high":
            color = "#DB2777"
            sector = "Creator-High"
        else:
            color = "#F9A8D4"
            sector = "Creator-Low"

    else:
        level = get_level(energy)

        if level == "high":
            color = "#EA580C"
            sector = "Explorer-High"
        else:
            color = "#FDBA74"
            sector = "Explorer-Low"

    # =========================
    # 🕒 時間帯判定
    # =========================
    hour = datetime.now().hour

    if 5 <= hour < 11:
        time_zone = "morning"
    elif 11 <= hour < 17:
        time_zone = "day"
    elif 17 <= hour < 22:
        time_zone = "evening"
    else:
        time_zone = "night"

    # =========================
    # 🎲 コメント辞書
    # =========================
    comments_dict = {

        "Analyst": {
            "morning": ["思考がクリア", "分析力が高い", "静かに集中"],
            "day": ["判断が正確", "論理が強い", "冷静な対応"],
            "evening": ["振り返りが深い", "洞察が鋭い", "整理が上手い"],
            "night": ["内省が進む", "思考が深まる", "静かな集中"]
        },

        "Leader": {
            "morning": ["行動力MAX", "決断が早い", "前に進む日"],
            "day": ["周囲を引っ張る", "勢いあり", "主導権あり"],
            "evening": ["成果を出す", "達成感あり", "流れ良い"],
            "night": ["明日へ準備", "戦略思考", "余裕あり"]
        },

        "Empath": {
            "morning": ["優しさが出る", "共感力高い", "人に寄り添う"],
            "day": ["対人運良い", "空気を読む", "安心感あり"],
            "evening": ["癒しの時間", "感情が豊か", "人との繋がり"],
            "night": ["静かな安心", "心が落ち着く", "優しい時間"]
        },

        "Reflector": {
            "morning": ["ゆっくりでOK", "無理しない", "整える時間"],
            "day": ["自分ペース", "内側を大事に", "静かに進む"],
            "evening": ["回復モード", "休むのも大事", "整ってきた"],
            "night": ["深いリラックス", "リセット時間", "回復優先"]
        },

        "Creator": {
            "morning": ["アイデア湧く", "感性が光る", "自由な発想"],
            "day": ["創造力高い", "表現が良い", "ひらめきあり"],
            "evening": ["作品モード", "没頭できる", "世界観あり"],
            "night": ["感性MAX", "独自性強い", "イメージ広がる"]
        },

        "Explorer": {
            "morning": ["好奇心高い", "新しい発見", "動き出す"],
            "day": ["変化に強い", "柔軟対応", "広がる日"],
            "evening": ["新しい視点", "気付きあり", "流れに乗る"],
            "night": ["自由時間", "探求モード", "ワクワク"]
        }
    }


    # =========================
    # 🎯 ランダム選択
    # =========================
    base_type = personality.split()[1]  # 🔬 Analyst → Analyst

    comment_pool = comments_dict.get(base_type, {}).get(time_zone, ["安定しています"])

    selected_comments = random.sample(comment_pool, min(3, len(comment_pool)))


    # =========================
    # レスポンス
    # =========================
    return {
        "message": f"受信OK: {file.filename}",
        "result": {
            "type": personality,
            "color": color,
            "sector": sector,
            "comments": selected_comments,
            "time_zone": time_zone,
            "scores": {
                "Energy": energy,
                "Emotion": emotion,
                "Focus": focus,
                "Social": social,
                "Calm": 100 - stress
            },
            "raw": result_raw
        }
    }

# ===============================
# 4.0 音声アップロード
# ===============================
@app.route("/upload", methods=["POST"])
def upload_full():
    try:
        print("=== UPLOAD START ===")

        global engine
        if engine is None:
            engine = VoiceStateEngine()


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
# 5.0 health check
# ===============================
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ===============================
# 6.0 起動
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
    



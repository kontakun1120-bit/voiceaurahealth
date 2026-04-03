# ==========================================================
# app_web.py（VoiceAuraHealth mini ベータ版 2.1
# ==========================================================

# ==========================================================
# 0.0 import
# ==========================================================
from flask import Flask, render_template, request, jsonify
import os, uuid, json, tempfile
from datetime import datetime
from pydub import AudioSegment
# from openai import OpenAI

from voice_state_engine import VoiceStateEngine


# ==========================================================
# 0.1 初期化
# ==========================================================
app = Flask(__name__)
engine = VoiceStateEngine()
# client = OpenAI()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================================================
# 1.0 基本API
# ==========================================================
# ----------------------------------------------------------
# 1.1 index）
# ----------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ----------------------------------------------------------
# 1.2 サーバー準備確認
# ---------------------------------------------------------
@app.route("/api/ping")
def ping():
    return "ok"


# ----------------------------------------------------------
# 2.0 音声解析 音声アップロードAPI（Railway安定版）
# ----------------------------------------------------------
@app.route("/api/upload", methods=["POST"])
def upload_audio():

    path = None
    wav_path = None

    try:
        if "audio" not in request.files:
            return jsonify({"error": "no audio file"}), 400

        file = request.files["audio"]

        if file.filename == "":
            return jsonify({"error": "empty file"}), 400

        # 🔥 追加
        db = float(request.form.get("db", 50))

        # 🔥 OS対応（ここが神ポイント）
        temp_dir = tempfile.gettempdir()

        ext = file.filename.split(".")[-1].lower() if "." in file.filename else "webm"
        path = os.path.join(temp_dir, f"{uuid.uuid4()}.{ext}")
        file.save(path)

        base, _ = os.path.splitext(path)
        wav_path = f"{base}_c.wav"

        # 🔥 音声変換
        audio = AudioSegment.from_file(path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(wav_path, format="wav")

        # 🔥 解析
        result = engine.analyze_from_file(wav_path, db=db)
        
        response = format_result(result)

        # 🔥 表示 将来用（コメント機能）
#       comment = request.form.get("comment","")
        
        # 🔥 保存
#        save_session(response, "")
#        save_session(response, comment)

        return jsonify({"result": response})

    except Exception as e:
        print("🔥[UPLOAD ERROR]", e)   # Railwayログ用
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            if path and os.path.exists(path):
                os.remove(path)
            if wav_path and os.path.exists(wav_path):
                os.remove(wav_path)
        except:
            pass


# ==========================================================
# 3.0 LLM / AI 関連
# ==========================================================
# ----------------------------------------------------------
# 3.1 LLMコメント UIにボタン追加 API、LLM engine側
# ----------------------------------------------------------
@app.route("/api/llm_comment", methods=["POST"])
def llm_comment():

    try:
        data = request.json
        scores = data["scores"]

        return jsonify({
            "energy": engine.llm_energy(scores),
            "emotion": engine.llm_emotion(scores),
            "focus": engine.llm_focus(scores),
            "stress": engine.llm_stress(scores),
            "mental": engine.llm_mental_stress(scores),
            "summary": engine.llm_summary(scores)
        })

    except Exception as e:
        print("llm error:", e)
        return jsonify({"error":"error"})


# ----------------------------------------------------------
# 3.2  今日のまとめ（簡易）AI LLM
# ----------------------------------------------------------
@app.route("/api/day_summary")
def day_summary():

    data = load_all_sessions()

    today = datetime.now().strftime("%Y-%m-%d")

    today_data = [
        d for d in data if d["timestamp"].startswith(today)
    ]

    if len(today_data) == 0:
        return jsonify({"summary":"データがありません"})

    # 🔥 平均
    avg_energy = sum(d["scores"]["Energy"] for d in today_data) / len(today_data)
    avg_mental = sum(d["scores"].get("MentalStress",0) for d in today_data) / len(today_data)

    # 🔥 コメント
    if avg_mental > 60:
        txt = "今日はやや負荷が高めです。無理せず過ごしましょう。"
    elif avg_mental > 40:
        txt = "適度な負荷の一日でした。"
    else:
        txt = "比較的安定した一日でした。"

    return jsonify({"summary": txt})


# ----------------------------------------------------------
# 3.3  朝昼夜まとめ（精密版・構造）AI LLM
# ----------------------------------------------------------
@app.route("/api/day_summary_detail")
def day_summary_detail():

    data = load_all_sessions()
    today = datetime.now().strftime("%Y-%m-%d")

    today_data = [d for d in data if d["timestamp"].startswith(today)]

    if not today_data:
        return jsonify({"summary": "データがありません"})

    zones = {"朝": [], "昼": [], "夜": []}

    for d in today_data:
        z = d.get("zone", "")
        if z in zones:
            zones[z].append(d)

    result = {}

    for k, v in zones.items():
        if v:
            result[k] = {
                "mental": sum(d["scores"].get("MentalStress",0) for d in v) / len(v),
                "energy": sum(d["scores"].get("Energy",0) for d in v) / len(v),
            }

    return jsonify({"data": result})
 

# ----------------------------------------------------------
# 3.4 GPT自然文化 GPT接続 LLM 仮
# ---------------------------------------------------------- 
@app.route("/api/day_summary_ai")
def day_summary_ai():

    res = day_summary_detail().get_json()
    data = res.get("data", {})

    if not data:
        return jsonify({"summary": "データが不足しています"})

    base = build_day_insight(data)

    # 🔥 仮AI（自然文化）
    if "昼" in base:
        txt = "昼に少し負荷がかかりやすいようです。無理をせず過ごしてくださいね。"
    elif "朝" in base:
        txt = "朝にやや負荷が見られます。ゆっくりスタートがおすすめです。"
    else:
        txt = "夜に疲れが出やすいようです。リラックスを意識すると良さそうです。"

    return jsonify({"summary": txt})


# ==========================================================
# 4.0 セッション管理
# ==========================================================
# ----------------------------------------------------------
# 4.1 前回データ取得
# ----------------------------------------------------------
def load_previous_session():
    try:
        if not os.path.exists("sessions"):
            return None

        files = sorted(
            [f for f in os.listdir("sessions") if f.endswith(".json")],
            reverse=True
        )

        if len(files) == 0:
            return None

        with open(f"sessions/{files[0]}", encoding="utf-8") as f:
            return json.load(f)

    except:
        return None


# ----------------------------------------------------------
# 4.2 全セッション読み込み
# ----------------------------------------------------------
def load_all_sessions():

    data = []

    try:
        if not os.path.exists("sessions"):
            return []

        files = sorted(
            [f for f in os.listdir("sessions") if f.endswith(".json")]
        )

        for f in files:
            try:
                with open(f"sessions/{f}", encoding="utf-8") as file:
                    j = json.load(file)
                    data.append(j)
            except:
                continue

    except Exception as e:
        print("load_all_sessions error:", e)

    return data


# ----------------------------------------------------------
# 4.3 日記save　Flask API追加
# ---------------------------------------------------------
@app.route("/api/save_comment", methods=["POST"])
def save_comment():

    hour = datetime.now().hour

    if hour < 10:
        zone = "朝"
    elif hour < 17:
        zone = "昼"
    else:
        zone = "夜"

    try:
        data = request.json

        session = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "zone": zone, 
            "scores": data["scores"],
            "vector192": data.get("vector192", []),
            "summary": data.get("summary", ""),
            "user_comment": data.get("comment", "")
        }

        os.makedirs("sessions", exist_ok=True)

        path = f"sessions/{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False, indent=2)

        return jsonify({"status":"ok"})

    except Exception as e:
        print("save error:", e)
        return jsonify({"error":str(e)})


# ----------------------------------------------------------
# 4.4   日記sessions　Flask API追加
# ---------------------------------------------------------
@app.route("/api/sessions")
def get_sessions():

    data = []

    try:
        if not os.path.exists("sessions"):
            return jsonify({"data":[]})

        files = sorted([f for f in os.listdir("sessions") if f.endswith(".json")], reverse=True)

        for f in files:
            try:
                with open(f"sessions/{f}", encoding="utf-8") as file:
                    j = json.load(file)

                    data.append({
                        "id": f,
                        "time": j["timestamp"],
                        "energy": j["scores"]["Energy"],
                        "summary": j.get("summary","")
                    })
            except:
                continue

    except Exception as e:
        print("sessions error:", e)

    return jsonify({"data": data})


# ==========================================================
# 5.0 分析ロジック
# ==========================================================
# ----------------------------------------------------------
# 5.1 比較
# ---------------------------------------------------------
def format_result(r):

    prev = load_previous_session()

    summary = engine.generate_empathy_summary(r)

    # 🔥 安全に比較
    if prev and isinstance(prev, dict) and "scores" in prev:
        try:
            msg = engine.compare_with_previous(
                r,
                prev["scores"]
            )
            summary = msg
        except Exception as e:
            print("compare error:", e)

    return {
        "scores":{
            "Energy":r["Energy"],
            "Emotion":r["Emotion"],
            "Focus":r["Focus"],
            "Social":r["Social"],
            "Calm":100-r["Stress"],
            "Stress": r["Stress"],         # VoiceStress
            "MentalStress": r.get("MentalStress", 0)   # MentalStress
        },
        "summary": summary,
        "vector192":r.get("vector192",[]),
        "ring_meta": {
            "outer": "声の特徴（192次元）",
            "middle": "心理状態（6指標）",
            "inner": "意味分類（12セクター）"
        }
    }


# ----------------------------------------------------------
# 5.2 意味化最大ストレス
# ---------------------------------------------------------
def build_day_insight(data):

    # 最大ストレス帯
    worst = max(data.items(), key=lambda x: x[1]["mental"])[0]

    if worst == "昼":
        return "昼にストレスが高くなる傾向があります"
    elif worst == "朝":
        return "朝にやや負荷がかかっています"
    else:
        return "夜に疲れが出やすい状態です"


# ----------------------------------------------------------
# 5.3 指標ごとのコメント
# ---------------------------------------------------------
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


# ==========================================================
# 6.0 履歴・分析API
# ==========================================================
# ----------------------------------------------------------
# 6.1 日記　Flask API追加
# ----------------------------------------------------------
@app.route("/api/energy_trend")
def trend():

    data = []

    try:
        if not os.path.exists("sessions"):
            return jsonify({"data":[]})

        files = sorted(
            [f for f in os.listdir("sessions") if f.endswith(".json")],
            reverse=True
        )

        for f in files:
            try:
                with open(f"sessions/{f}",encoding="utf-8") as file:
                    j=json.load(file)

                    data.append({
                        "time":j["timestamp"],
                        "energy":j["scores"]["Energy"],
                        "zone": j.get("zone","")
                    })
            except Exception as e:
                print("skip file:", f, e)
                continue

    except Exception as e:
        print("trend error:", e)

    return jsonify({"data": data})


# ----------------------------------------------------------
# 6.2 日記sessions　Flask 詳細API
# ----------------------------------------------------------
@app.route("/api/session/<sid>")
def get_session_detail(sid):

    try:
        path = f"sessions/{sid}"

        if not os.path.exists(path):
            return jsonify({"error":"not found"})

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        return jsonify({"data": data})

    except Exception as e:
        print("detail error:", e)
        return jsonify({"error": str(e)})


# ----------------------------------------------------------
# 6.3 日記sessions　Flask 詳細API 追加
# ----------------------------------------------------------
@app.route("/api/session_diff/<sid>")
def get_session_diff(sid):

    try:
        files = sorted(
            [f for f in os.listdir("sessions") if f.endswith(".json")],
            reverse=True
        )

        if len(files) < 2:
            return jsonify({"diff": {}})

        # 対象ファイル位置
        idx = files.index(sid)
        if idx == len(files) - 1:
            return jsonify({"diff": {}})

        def load(f):
            with open(f"sessions/{f}", encoding="utf-8") as file:
                return json.load(file)

        current = load(files[idx])
        prev = load(files[idx + 1])

        diff = {}

        for k in current["scores"]:
            diff[k] = current["scores"][k] - prev["scores"][k]

        return jsonify({"diff": diff})

    except Exception as e:
        print("detail diff error:", e)
        return jsonify({"diff": {}})


# ----------------------------------------------------------
# 6.4 昨日との差　Flask API追加
# ----------------------------------------------------------
@app.route("/api/diff")
def get_diff():

    try:
        if not os.path.exists("sessions"):
            return jsonify({"diff": 0})

        files = sorted(
            [f for f in os.listdir("sessions") if f.endswith(".json")],
            reverse=True
        )

        if len(files) < 2:
            return jsonify({"diff": 0})

        def load(f):
            with open(f"sessions/{f}", encoding="utf-8") as file:
                return json.load(file)

        latest = load(files[0])
        prev = load(files[1])

        diff = latest["scores"]["Energy"] - prev["scores"]["Energy"]

        return jsonify({"diff": diff})

    except Exception as e:
        print("diff error:", e)
        return jsonify({"diff": 0})


# ==========================================================
# 7.0 管理API
# ==========================================================
# ----------------------------------------------------------
# 7.1 履歴 一行、全削除　Flask API追加
# ----------------------------------------------------------
@app.route("/api/delete_session/<id>", methods=["DELETE"])
def delete_session(id):

    path = f"sessions/{id}"

    if os.path.exists(path):
        os.remove(path)

    return jsonify({"status":"ok"})


# ----------------------------------------------------------
# 7.2 削除  
# ---------------------------------------------------------    
@app.route("/api/delete_all_sessions", methods=["DELETE"])
def delete_all_sessions():

    if os.path.exists("sessions"):
        for f in os.listdir("sessions"):
            if f.endswith(".json"):
                os.remove(f"sessions/{f}")

    return jsonify({"status":"ok"})


# ==========================================================
# 8.0 保存系
# ==========================================================
# ----------------------------------------------------------
# 8.1 192次元のベクトルの保存関数
# ----------------------------------------------------------
def save_session(result, comment=""):

    try:
        session = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scores": result["scores"],
            "vector192": result.get("vector192", []),
            "summary": result.get("summary", ""),
            "user_comment": comment  # 👈追加
        }

        # フォルダ作成
        os.makedirs("sessions", exist_ok=True)

        filename = datetime.now().strftime("session_%Y%m%d_%H%M%S.json")
        path = os.path.join("sessions", filename)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print("⚠ save error:", e)


# ==========================================================
# 9.0 run
# ==========================================================
if __name__ == "__main__":
    app.run(debug=True)
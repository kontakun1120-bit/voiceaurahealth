# ==========================================================
# app_web.py（VoiceAuraHealth mini v2）
# ==========================================================

from flask import Flask, render_template, request, jsonify
import os, uuid, json
from datetime import datetime
from pydub import AudioSegment
from voice_state_engine import VoiceStateEngine
import tempfile

app = Flask(__name__)
engine = VoiceStateEngine()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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

        # 🔥 OS対応（ここが神ポイント）
        temp_dir = tempfile.gettempdir()

        path = os.path.join(temp_dir, f"{uuid.uuid4()}.webm")
        file.save(path)

        wav_path = path.replace(".wav","_c.wav")

        # 🔥 音声変換
        audio = AudioSegment.from_file(path, format="webm")
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(wav_path, format="wav")

        # 🔥 解析
        result = engine.analyze_from_file(wav_path)
        response = format_result(result)

        # 🔥 表示
        comment = request.form.get("comment","")
        
        # 🔥 保存
#        save_session(response, comment)

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
# 3.0 前回データ取得
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

# --------------------
def format_result(r):
    return {
        "scores":{
            "Energy":r["Energy"],
            "Emotion":r["Emotion"],
            "Focus":r["Focus"],
            "Social":r["Social"],
            "Calm":100-r["Stress"],
            "Stress": r["Stress"],   # 追加
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
# 2.0 日記　Flask API追加
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
                        "energy":j["scores"]["Energy"]
                    })
            except Exception as e:
                print("skip file:", f, e)
                continue

    except Exception as e:
        print("trend error:", e)

    return jsonify({"data": data})


# ----------------------------------------------------------
# 2.1 日記save　Flask API追加
# ----------------------------------------------------------
@app.route("/api/save_comment", methods=["POST"])
def save_comment():

    try:
        data = request.json

        session = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
# 2.2.1 日記sessions　Flask API追加
# ----------------------------------------------------------
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


# ----------------------------------------------------------
# 2.2.2 日記sessions　Flask 詳細API
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
# 2.2.3 日記sessions　Flask 詳細API 追加
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
# 2.3 昨日との差　Flask API追加
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


# ----------------------------------------------------------
# 2.4 履歴 一行、全削除　Flask API追加
# ----------------------------------------------------------
@app.route("/api/delete_session/<id>", methods=["DELETE"])
def delete_session(id):

    path = f"sessions/{id}"

    if os.path.exists(path):
        os.remove(path)

    return jsonify({"status":"ok"})
    
@app.route("/api/delete_all_sessions", methods=["DELETE"])
def delete_all_sessions():

    if os.path.exists("sessions"):
        for f in os.listdir("sessions"):
            if f.endswith(".json"):
                os.remove(f"sessions/{f}")

    return jsonify({"status":"ok"})

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
# 4.0 192次元のベクトルの保存関数
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

# ----------------------------------------------------------
# 5.0 run
# ----------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
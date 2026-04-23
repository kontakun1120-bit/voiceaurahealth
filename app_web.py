from flask import Flask, render_template, request, jsonify
import os
import uuid
from pydub import AudioSegment
from datetime import datetime
from zoneinfo import ZoneInfo
from core.aura_engine import AuraEngine

app = Flask(__name__)
engine = AuraEngine()

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

def now_jst():
    return datetime.now(ZoneInfo("Asia/Tokyo"))


def convert_to_wav(input_path: str, output_path: str, mime=None):
    ext = os.path.splitext(input_path)[1].lower()

    fmt = None

    if mime:
        mime = mime.lower()
        if "webm" in mime:
            fmt = "webm"
        elif "mp4" in mime:
            fmt = "mp4"
        elif "aac" in mime:
            fmt = "aac"
        elif "wav" in mime:
            fmt = "wav"

    if not fmt:
        if ext == ".webm":
            fmt = "webm"
        elif ext == ".mp4":
            fmt = "mp4"
        elif ext == ".aac":
            fmt = "aac"
        elif ext == ".wav":
            fmt = "wav"

    if not fmt:
        raise ValueError(f"unsupported audio format: mime={mime}, ext={ext}")

    audio = AudioSegment.from_file(input_path, format=fmt)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(output_path, format="wav")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    raw_path = None
    wav_path = None

    try:
        if "audio" not in request.files:
            return jsonify({"ok": False, "error": "audioなし"}), 400

        file = request.files["audio"]

        if not file or file.filename == "":
            return jsonify({"ok": False, "error": "ファイル未選択"}), 400

        ext = os.path.splitext(file.filename)[1].lower()
        if ext == "":
            ext = ".wav"

        uid = uuid.uuid4().hex
        raw_path = os.path.join(TEMP_DIR, f"{uid}{ext}")
        wav_path = os.path.join(TEMP_DIR, f"{uid}.wav")

        file.save(raw_path)

        convert_to_wav(raw_path, wav_path, mime=file.content_type)

        sigma = float(request.form.get("sigma", 2))
        upscale = int(request.form.get("upscale", 1))
        psy_weight = float(request.form.get("psy", 0.5))
        contrast = float(request.form.get("contrast", 1.0))

        result = engine.analyze_from_file(
            wav_path=wav_path,
            sigma=sigma,
            upscale=upscale,
            psy_weight=psy_weight,
            contrast=contrast,
        )

        return jsonify({
            "ok": True,
            **result
        })

    except Exception as e:
        print("🔥 ERROR:", e)
        import traceback
        traceback.print_exc()

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

    finally:
        for p in [raw_path, wav_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

@app.route("/lp")
def lp():
    return render_template("lp.html")


if __name__ == "__main__":
    app.run(debug=True)
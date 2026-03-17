
import numpy as np
import sounddevice as sd
import torchaudio
import soundfile as sf

from speechbrain.inference.speaker import EncoderClassifier
from core.voice_state_engine import VoiceStateEngine
from flask import Flask, jsonify, render_template


app = Flask(__name__)

SR = 16000
SECONDS = 5
WAV_FILE = "voice_web.wav"

classifier = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb"
)

engine = VoiceStateEngine()

@app.route("/")
def index():
    return render_template("index.html")
    
@app.route("/analyze")

def analyze():

    print("🎤 Recording...")

    # 録音
    audio = sd.rec(
        int(SECONDS * SR),
        samplerate=SR,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    audio = audio.flatten()

    sf.write(WAV_FILE, audio, SR)

    # embedding
    signal, fs = torchaudio.load(WAV_FILE)

    embedding = classifier.encode_batch(signal)

    embedding = embedding.squeeze().detach().cpu().numpy()

    # Voice State
    state = engine.predict(embedding)

    return jsonify(state)


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)
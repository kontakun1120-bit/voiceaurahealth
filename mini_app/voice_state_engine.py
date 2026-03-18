# ==========================================================
# VoiceAura VoiceState Engine（本物版）
# patient6/core/voice_state_engine.py
# ==========================================================

import wave
import numpy as np


class VoiceStateEngine:

    # ------------------------------------------------------
    # 1 init
    # ------------------------------------------------------
    def __init__(self):
        self.scale = 100

    # ------------------------------------------------------
    # 2 外部API（ファイル）
    # ------------------------------------------------------
    def analyze_from_file(self, path):
        audio = self._load_wav_mono(path)
        return self._analyze_core(audio)


    # =====================================================
    # 1.1.0 wav読み込み
    # =====================================================
    def load_wav(self, path):
        with wave.open(path, 'rb') as wf:
            n_channels = wf.getnchannels()
            framerate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())

        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32)

        if n_channels == 2:
            audio = audio.reshape(-1, 2).mean(axis=1)

        audio /= 32768.0

        return audio, framerate

    # =====================================================
    # 1.2.0 特徴量抽出（最小）
    # =====================================================
    def extract_features(self, audio):

        rms = np.sqrt(np.mean(audio**2))              # 音量
        zcr = np.mean(np.abs(np.diff(np.sign(audio)))) # ノイズ/活発度

        return {
            "rms": float(rms),
            "zcr": float(zcr)
        }

    # =====================================================
    # 1.3.0 スコア変換（簡易モデル）
    # =====================================================
    def calc_scores(self, feat):

        stress = int(np.clip((1 - feat["rms"]) * 100, 0, 100))
        energy = int(np.clip(feat["rms"] * 150, 0, 100))
        emotion = int(np.clip(feat["zcr"] * 100, 0, 100))
        focus = int(np.clip((1 - feat["zcr"]) * 100, 0, 100))
        social = int(np.clip(feat["rms"] * 120, 0, 100))
        fatigue = int(np.clip((1 - feat["rms"]) * 120, 0, 100))
        arousal = int(np.clip(feat["zcr"] * 80, 0, 100))

        return {
            "stress": stress,
            "energy": energy,
            "emotion": emotion,
            "focus": focus,
            "social": social,
            "fatigue": fatigue,
            "arousal": arousal
        }

    # =====================================================
    # 1.4.0 メイン
    # =====================================================
    def analyze(self, wav_path):

        audio, sr = self.load_wav(wav_path)
        feat = self.extract_features(audio)
        scores = self.calc_scores(feat)

        return scores

    # ------------------------------------------------------
    # 3 WAV読み込み
    # ------------------------------------------------------
    def _load_wav_mono(self, path):
        with wave.open(path, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()
            framerate = wf.getframerate()
            raw = wf.readframes(n_frames)

        if sampwidth != 2:
            raise ValueError("16bit PCM WAVのみ対応です")

        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32)

        if n_channels == 2:
            audio = audio.reshape(-1, 2).mean(axis=1)

        # -1.0 ～ 1.0 に正規化
        audio = audio / 32768.0

        return audio

    # ------------------------------------------------------
    # 4 コア処理
    # ------------------------------------------------------
    def _analyze_core(self, audio):
        vector192 = self._audio_to_vector192(audio)
        return self.predict(vector192)

    # ------------------------------------------------------
    # 5 音声 → 簡易192次元
    # ------------------------------------------------------
    def _audio_to_vector192(self, audio):
        if len(audio) == 0:
            return np.zeros(192, dtype=np.float32)

        # 音量の極端値を少し抑える
        audio = np.clip(audio, -1.0, 1.0)

        # 長さを192に揃える
        src_x = np.linspace(0.0, 1.0, num=len(audio), dtype=np.float32)
        dst_x = np.linspace(0.0, 1.0, num=192, dtype=np.float32)
        vec = np.interp(dst_x, src_x, audio).astype(np.float32)

        # DC成分を除去
        vec = vec - np.mean(vec)

        return vec

    # ------------------------------------------------------
    # 6 normalize
    # ------------------------------------------------------
    def _normalize(self, v):
        v = np.asarray(v, dtype=float)
        norm = np.linalg.norm(v)

        if norm == 0:
            return v

        return v / norm

    # ------------------------------------------------------
    # 7 Energy
    # ------------------------------------------------------
    def _energy(self, v):
        val = np.mean(np.abs(v)) * 800
        return val

    # ------------------------------------------------------
    # 8 Stress
    # ------------------------------------------------------
    def _stress(self, v):
        val = np.std(v) * 600
        return val

    # ------------------------------------------------------
    # 9 Emotion
    # ------------------------------------------------------
    def _emotion(self, v):
        val = abs(np.mean(v)) * 1200
        return val

    # ------------------------------------------------------
    # 10 Focus
    # ------------------------------------------------------
    def _focus(self, v):
        val = (1.0 / (1.0 + np.var(v))) * 100
        return val

    # ------------------------------------------------------
    # 11 Social
    # ------------------------------------------------------
    def _social(self, v):
        val = (np.max(v) - np.min(v)) * 200
        return val

    # ------------------------------------------------------
    # 12 clamp
    # ------------------------------------------------------
    def _clamp(self, x):
        x = max(0, min(self.scale, x))
        return int(x)

    # ------------------------------------------------------
    # 13 personality type
    # ------------------------------------------------------
    def _personality_type(self, energy, emotion, focus, social, stress):
        if focus > 70:
            return "🔬 Analyst"
        elif social > 70:
            return "🤝 Empath"
        elif energy > 70:
            return "🔥 Leader"
        elif stress < 30:
            return "🌱 Reflector"
        elif emotion > 60:
            return "🎨 Creator"
        else:
            return "🧭 Explorer"

    # ------------------------------------------------------
    # 14 color sector
    # ------------------------------------------------------
    def _color_sector(self, energy, emotion, focus, social, stress):
        score = (energy + emotion + focus + social) / 4

        sectors = [
            ("#8F00FF", "violet", "直感・ビジョン・想像"),
            ("#001F54", "navy", "思考・分析"),
            ("#0077FF", "blue", "冷静・論理"),
            ("#00B7C2", "turquoise", "対人感覚"),
            ("#00A86B", "emerald", "会話力"),
            ("#7FFF00", "lime", "共感"),
            ("#FFD300", "yellow", "自信"),
            ("#FFD700", "gold", "存在感"),
            ("#FF8C00", "orange", "満足感"),
            ("#FF6F61", "coral", "身体感覚"),
            ("#FF0000", "red", "行動力"),
            ("#FF00FF", "magenta", "愛情・包容"),
        ]

        idx = int(score / 100 * 11)
        idx = max(0, min(11, idx))

        color, name, desc = sectors[idx]
        return f"{name} : {desc}"

    # ------------------------------------------------------
    # 15 predict
    # ------------------------------------------------------
    def predict(self, vector192):
        v = self._normalize(vector192)

        energy = self._energy(v)
        stress = self._stress(v)
        emotion = self._emotion(v)
        focus = self._focus(v)
        social = self._social(v)

        ptype = self._personality_type(energy, emotion, focus, social, stress)
        pcolor = self._color_sector(energy, emotion, focus, social, stress)

        fatigue = (100 - energy + stress) / 2
        arousal = (energy + emotion) / 2

        stress_clamped = self._clamp(stress)

        return {
            "Energy": self._clamp(energy),
            "Stress": stress_clamped,
            "Emotion": self._clamp(emotion),
            "Focus": self._clamp(focus),
            "Social": self._clamp(social),
            "Fatigue": self._clamp(fatigue),
            "Arousal": self._clamp(arousal),
            "Personality": ptype,
            "ColorSector": pcolor,
            "StressComment": self.stress_comment(stress_clamped),
        }

    # ------------------------------------------------------
    # 16 stress comment
    # ------------------------------------------------------
    def stress_comment(self, stress):
        stress = int(stress)

        if stress < 20:
            return "とてもリラックスした声です。"
        elif stress < 40:
            return "ストレスは低めです。"
        elif stress < 60:
            return "中程度のストレスです。"
        elif stress < 80:
            return "ストレス高めです。"
        else:
            return "強いストレス状態です。"


# ==========================================================
# test
# ==========================================================
if __name__ == "__main__":
    engine = VoiceStateEngine()
    state = engine.analyze_from_file("../static/voice_web.wav")

    print("\nVoice State\n")
    for k, v in state.items():
        print(f"{k:12} {v}")
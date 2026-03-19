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
        feat = self.extract_features(audio)

        return self.analyze_with_time(path)
#        return self.calc_scores(feat)       #  追加


    # =====================================================
    # 3.0 wav読み込み
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

    # ------------------------------------------------------
    # 3.1 WAV読み込み
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
    # 3.2 分割処理
    # ------------------------------------------------------
    def _split_audio(self, audio, num_segments=5):
        length = len(audio)
        segment_size = length // num_segments

        segments = []
        for i in range(num_segments):
            start = i * segment_size
            end = (i + 1) * segment_size
            segments.append(audio[start:end])

        return segments

    # ------------------------------------------------------
    # 3.3 時系列解析
    # -----------------------------------------------------
    def analyze_with_time(self, path):
        audio = self._load_wav_mono(path)

        segments = self._split_audio(audio, 5)

        results = []
        for seg in segments:
            feat = self.extract_features(seg)
            score = self.calc_scores(feat)
            results.append(score)

        # 平均
        final = {}
        for key in results[0].keys():
            final[key] = int(np.mean([r[key] for r in results]))

        # 🔥 ここ追加（最重要）
        stress_comment, personality, color = self.generate_comment(final)

        final["StressComment"] = stress_comment
        final["Personality"] = personality
        final["ColorSector"] = color

        return final


    # =====================================================
    # 4 特徴量抽出
    # =====================================================
    def extract_features(self, audio):

        rms = np.sqrt(np.mean(audio**2))
        zcr = np.mean(np.abs(np.diff(np.sign(audio))))
        std = np.std(audio)
        peak = np.max(np.abs(audio))
        dynamic = peak - rms

        return {
            "rms": float(rms),
            "zcr": float(zcr),
            "std": float(std),
            "peak": float(peak),
            "dynamic": float(dynamic)
        }

#    # =====================================================
#    # 1.2.0 特徴量抽出（最小）
#    # =====================================================
#    def extract_features(self, audio):
#
#        rms = np.sqrt(np.mean(audio**2))              # 音量
#        zcr = np.mean(np.abs(np.diff(np.sign(audio)))) # ノイズ/活発度
#
#        return {
#            "rms": float(rms),
#            "zcr": float(zcr)
#        }


#    # =====================================================
#    # 5 スコア変換
#    # =====================================================
    def calc_scores(self, feat):

        energy = (feat["rms"] * 120 + feat["std"] * 80)
        stress = (feat["std"] * 120 + feat["zcr"] * 80)
        emotion = (feat["zcr"] * 120 + feat["dynamic"] * 100)
        focus = (1 - feat["zcr"]) * 100
        social = (feat["rms"] * 100 + feat["peak"] * 50)
        fatigue = (1 - feat["rms"]) * 100 + feat["std"] * 50
        arousal = (feat["peak"] * 100 + feat["zcr"] * 50)

        return {
            "Energy": int(np.clip(energy, 0, 100)),
            "Stress": int(np.clip(stress, 0, 100)),
            "Emotion": int(np.clip(emotion, 0, 100)),
            "Focus": int(np.clip(focus, 0, 100)),
            "Social": int(np.clip(social, 0, 100)),
            "Fatigue": int(np.clip(fatigue, 0, 100)),
            "Arousal": int(np.clip(arousal, 0, 100))
        }

#    # =====================================================
#    # 1.3.0 スコア変換（簡易モデル）
#    # =====================================================
#    def calc_scores(self, feat):
#
#        stress = int(np.clip((1 - feat["rms"]) * 100, 0, 100))
#        energy = int(np.clip(feat["rms"] * 150, 0, 100))
#        emotion = int(np.clip(feat["zcr"] * 100, 0, 100))
#        focus = int(np.clip((1 - feat["zcr"]) * 100, 0, 100))
#        social = int(np.clip(feat["rms"] * 120, 0, 100))
#        fatigue = int(np.clip((1 - feat["rms"]) * 120, 0, 100))
#        arousal = int(np.clip(feat["zcr"] * 80, 0, 100))
#
#        return {
#            "stress": stress,
#            "energy": energy,
#            "emotion": emotion,
#            "focus": focus,
#            "social": social,
#            "fatigue": fatigue,
#            "arousal": arousal
#        }

    # =====================================================
    # 6.0 メイン
    # =====================================================
    def analyze(self, wav_path):

        audio, sr = self.load_wav(wav_path)
        feat = self.extract_features(audio)
        scores = self.calc_scores(feat)

        # 👇追加
        stress_comment, personality, color = self.generate_comment(scores)

        scores["StressComment"] = stress_comment
        scores["Personality"] = personality
        scores["ColorSector"] = color

        return scores

    # ------------------------------------------------------
    # 7.0 コア処理
    # ------------------------------------------------------
    def _analyze_core(self, audio):
        vector192 = self._audio_to_vector192(audio)
        return self.predict(vector192)

    # ------------------------------------------------------
    # 7.1 音声 → 簡易192次元
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
    # 7.2 normalize
    # ------------------------------------------------------
    def _normalize(self, v):
        v = np.asarray(v, dtype=float)
        norm = np.linalg.norm(v)

        if norm == 0:
            return v

        return v / norm

    # ------------------------------------------------------
    # 8.0 Energy
    # ------------------------------------------------------
    def _energy(self, v):
        val = np.mean(np.abs(v)) * 800
        return val

    # ------------------------------------------------------
    # 8.1 Stress
    # ------------------------------------------------------
    def _stress(self, v):
        val = np.std(v) * 600
        return val

    # ------------------------------------------------------
    # 8.2 Emotion
    # ------------------------------------------------------
    def _emotion(self, v):
        val = abs(np.mean(v)) * 1200
        return val

    # ------------------------------------------------------
    # 8.3 Focus
    # ------------------------------------------------------
    def _focus(self, v):
        val = (1.0 / (1.0 + np.var(v))) * 100
        return val

    # ------------------------------------------------------
    # 8.4 Social
    # ------------------------------------------------------
    def _social(self, v):
        val = (np.max(v) - np.min(v)) * 200
        return val

    # ------------------------------------------------------
    # 8.5 clamp
    # ------------------------------------------------------
    def _clamp(self, x):
        x = max(0, min(self.scale, x))
        return int(x)


    # ------------------------------------------------------
    # 9.0 総合コメント
    # ------------------------------------------------------
    def generate_comment(self, scores):

        stress = scores["Stress"]
        energy = scores["Energy"]
        fatigue = scores["Fatigue"]

        # =========================
        # ストレスコメント
        # =========================
        if stress > 70:
            stress_comment = "⚠ ストレス高め。休息推奨"
        elif stress > 40:
            stress_comment = "ややストレスあり"
        else:
            stress_comment = "ストレス安定"

        # =========================
        # 人格タイプ（簡易版）
        # =========================
        if energy > 70:
            personality = "🔥 リーダー型 タイプ"
        elif fatigue > 70:
            personality = "🌱 内省型 タイプ"
        elif scores["Emotion"] > 60:
            personality = "🎨 創造型 タイプ"
        else:
            personality = "🔬 分析型 タイプ"

        # =========================
        # カラーセクター（簡易）
        # =========================
        if scores["Arousal"] > 70:
            color = "🔴 高覚醒状態"
        elif scores["Arousal"] < 30:
            color = "🔵 低覚醒状態"
        else:
            color = "🟢 安定状態"

        return stress_comment, personality, color

    # ------------------------------------------------------
    # 9.0 personality type
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
    # 9.1 color sector
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
    # 10.0 predict
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
    # 10.2 stress comment
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
# 11.0 test
# ==========================================================
if __name__ == "__main__":
    engine = VoiceStateEngine()
    state = engine.analyze_from_file("../static/voice_web.wav")

    print("\nVoice State\n")
    for k, v in state.items():
        print(f"{k:12} {v}")
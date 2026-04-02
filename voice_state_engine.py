# ==========================================================
# VoiceAura VoiceState Engine（predict一本化・完全版）
# mini_app/voice_state_engine.py
# ==========================================================

import wave
import numpy as np
import random


class VoiceStateEngine:
    """
    VoiceAura mini 用の音声状態推定エンジン

    設計方針
    ---------------------------------
    1. 音声を 16bit PCM mono WAV として読む
    2. 5秒音声を5分割して時系列平均する
    3. 各分割音声を predict() に通す
    4. predict() 内で
       - 192次元ベクトル化
       - 正規化
       - 特徴量抽出
       - 重み付きスコア化
       を一貫して実施する
    """

    # ------------------------------------------------------
    # 1.0 init
    # ------------------------------------------------------
    def __init__(self):
        self.scale = 100

    # ------------------------------------------------------
    # 2.0 外部公開API
    # ------------------------------------------------------
    def analyze_from_file(self, path: str) -> dict:
        return self.analyze_with_time(path)

    # ------------------------------------------------------
    # 3.0 WAV読み込み
    # ------------------------------------------------------
    def load_wav(self, path: str):
        with wave.open(path, "rb") as wf:
            n_channels = wf.getnchannels()
            framerate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())

        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32)

        if n_channels == 2:
            audio = audio.reshape(-1, 2).mean(axis=1)

        audio /= 32768.0
        return audio, framerate

    # ------------------------------------------------------
    # 3.1 WAV読み込み（mono）
    # ------------------------------------------------------
    def _load_wav_mono(self, path: str) -> np.ndarray:
        with wave.open(path, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        if sampwidth != 2:
            raise ValueError("16bit PCM WAVのみ対応です")

        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32)

        if n_channels == 2:
            audio = audio.reshape(-1, 2).mean(axis=1)

        audio = audio / 32768.0
        return audio

    # ------------------------------------------------------
    # 3.2 分割処理
    # ------------------------------------------------------
    def _split_audio(self, audio: np.ndarray, num_segments: int = 5):
        length = len(audio)

        if length == 0:
            return [np.zeros(1, dtype=np.float32) for _ in range(num_segments)]

        segment_size = max(1, length // num_segments)

        segments = []
        for i in range(num_segments):
            start = i * segment_size

            if i == num_segments - 1:
                end = length
            else:
                end = min((i + 1) * segment_size, length)

            seg = audio[start:end]

            if len(seg) == 0:
                seg = np.zeros(1, dtype=np.float32)

            segments.append(seg)

        return segments

    # ------------------------------------------------------
    # 3.3 時系列解析
    # ------------------------------------------------------
    def analyze_with_time(self, path: str) -> dict:
        audio = self._load_wav_mono(path)
        segments = self._split_audio(audio, 5)

        results = []
        for seg in segments:
            score = self.predict(seg)
            results.append(score)

        score_keys = [
            "Energy",
            "Stress",
            "Emotion",
            "Focus",
            "Social",
            "Fatigue",
            "Arousal",
        ]

        final = {}
        
        for key in score_keys:
            final[key] = int(np.mean([r[key] for r in results]))

        # 🔥 vector192を平均して追加
        vectors = [r["vector192"] for r in results if "vector192" in r]

        if len(vectors) > 0:
            v_mean = np.mean(np.array(vectors), axis=0)
            final["vector192"] = v_mean.tolist()
        else:
            final["vector192"] = [0.0]*192

        stress_comment, personality, color = self.generate_comment(final)

        final["StressComment"] = stress_comment
        final["Personality"] = personality
        final["ColorSector"] = color

        return final
        


    # ------------------------------------------------------
    # 4.0 audio -> 192 vector
    # ------------------------------------------------------
    def _audio_to_vector192(self, audio: np.ndarray) -> np.ndarray:
        if len(audio) == 0:
            return np.zeros(192, dtype=np.float32)

        audio = np.clip(audio, -1.0, 1.0)

        src_x = np.linspace(0.0, 1.0, num=len(audio), dtype=np.float32)
        dst_x = np.linspace(0.0, 1.0, num=192, dtype=np.float32)
        vec = np.interp(dst_x, src_x, audio).astype(np.float32)

        vec = vec - np.mean(vec)
        return vec

    # ------------------------------------------------------
    # 4.1 normalize vector
    # ------------------------------------------------------
    def _normalize(self, v: np.ndarray) -> np.ndarray:
        v = np.asarray(v, dtype=np.float32)
        norm = np.linalg.norm(v)

        if norm == 0:
            return v

        return v / norm

    # ------------------------------------------------------
    # 4.2 scalar normalize
    # ------------------------------------------------------
    def _norm01(self, x: float, min_v: float, max_v: float) -> float:
        if max_v <= min_v:
            return 0.0

        x = max(min_v, min(float(x), max_v))
        return (x - min_v) / (max_v - min_v)

    # ------------------------------------------------------
    # 4.3 0-100 clamp
    # ------------------------------------------------------
    def _clamp(self, x: float) -> int:
        x = max(0.0, min(float(self.scale), float(x)))
        return int(round(x))

    # ------------------------------------------------------
    # 5.0 特徴量抽出
    # ------------------------------------------------------
    def _extract_core_features(self, v: np.ndarray) -> dict:
        if len(v) == 0:
            v = np.zeros(1, dtype=np.float32)

        abs_v = np.abs(v)

        rms = np.sqrt(np.mean(v ** 2))
        std = np.std(v)
        peak = np.max(abs_v)
        dynamic = peak - rms
        zcr = np.mean(np.abs(np.diff(np.sign(v)))) if len(v) > 1 else 0.0
        var = np.var(v)
        mean_abs = np.mean(abs_v)

        return {
            "rms": float(rms),
            "std": float(std),
            "peak": float(peak),
            "dynamic": float(dynamic),
            "zcr": float(zcr),
            "var": float(var),
            "mean_abs": float(mean_abs),
        }

    # ------------------------------------------------------
    # 5.1 重み付きスコア計算
    # ------------------------------------------------------
    def _calculate_scores(self, f: dict) -> dict:
        rms_n = self._norm01(f["rms"], 0.02, 0.35)
        std_n = self._norm01(f["std"], 0.01, 0.25)
        peak_n = self._norm01(f["peak"], 0.05, 0.90)
        dyn_n = self._norm01(f["dynamic"], 0.01, 0.60)
        zcr_n = self._norm01(f["zcr"], 0.01, 0.60)
        var_n = self._norm01(f["var"], 0.0001, 0.08)
        mean_abs_n = self._norm01(f["mean_abs"], 0.01, 0.30)

        energy = (0.45 * rms_n + 0.35 * dyn_n + 0.20 * mean_abs_n) ** 1.3  # 見える差

        stress = (0.40 * std_n + 0.35 * zcr_n + 0.25 * var_n) ** 1.3  # 見える差

        emotion = (0.45 * dyn_n + 0.35 * zcr_n + 0.20 * peak_n) ** 1.3  # 見える差

        focus = (
            0.55 * (1.0 - zcr_n) +
            0.45 * (1.0 - std_n)
        )

        social = (
            0.35 * rms_n +
            0.35 * peak_n +
            0.30 * dyn_n
        )

        fatigue = (
            0.55 * (1.0 - rms_n) +
            0.25 * std_n +
            0.20 * (1.0 - mean_abs_n)
        )

        arousal = (
            0.40 * peak_n +
            0.35 * std_n +
            0.25 * zcr_n
        )

        return {
            "Energy": self._clamp(energy * 100),
            "Stress": self._clamp(stress * 100),
            "Emotion": self._clamp(emotion * 100),
            "Focus": self._clamp(focus * 100),
            "Social": self._clamp(social * 100),
            "Fatigue": self._clamp(fatigue * 100),
            "Arousal": self._clamp(arousal * 100),
        }

    # ------------------------------------------------------
    # 6.0 personality type
    # ------------------------------------------------------
    def _personality_type(
        self,
        energy: int,
        emotion: int,
        focus: int,
        social: int,
        stress: int
    ) -> str:
        if focus > 70:
            return "🔬 分析型 タイプ"
        elif social > 70:
            return "🤝 共感型 タイプ"
        elif energy > 70:
            return "🔥 行動型 タイプ"
        elif stress < 30:
            return "🌱 内省型 タイプ"
        elif emotion > 60:
            return "🎨 創造型 タイプ"
        else:
            return "🧭 探索型 タイプ"

    # ------------------------------------------------------
    # 7.0 color sector
    # ------------------------------------------------------
    def _color_sector(
        self,
        energy: int,
        emotion: int,
        focus: int,
        social: int,
        stress: int
    ) -> str:
        score = (energy + emotion + focus + social) / 4.0

        sectors = [
            ("#8F00FF", "violet", "直感・ビジョン・想像"),
            ("#001F54", "navy", "思考・分析"),
            ("#0077FF", "blue", "冷静・論理"),
            ("#00B7C2", "turquoise", "対人感覚"),
            ("#00A86B", "green", "安定状態"),
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
    # 8.0 stress comment
    # ------------------------------------------------------
    def stress_comment(self, stress: int) -> str:
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

    # ------------------------------------------------------
    # 9.0 predict
    # ------------------------------------------------------
    def predict(self, audio: np.ndarray) -> dict:
        if len(audio) == 0:
            return {
                "Energy": 0,
                "Stress": 0,
                "Emotion": 0,
                "Focus": 0,
                "Social": 0,
                "Fatigue": 0,
                "Arousal": 0,
                "Personality": "🧭 探索型 タイプ",
                "ColorSector": "navy : 思考・分析",
                "StressComment": "音声が短すぎます。"
            }

        vector192 = self._audio_to_vector192(audio)

        v = vector192  # ←正規化外す。正規化を弱める。変化が出る
#        v = self._normalize(vector192)

        feat = self._extract_core_features(v)
        scores = self._calculate_scores(feat)

        ptype = self._personality_type(
            scores["Energy"],
            scores["Emotion"],
            scores["Focus"],
            scores["Social"],
            scores["Stress"],
        )

        pcolor = self._color_sector(
            scores["Energy"],
            scores["Emotion"],
            scores["Focus"],
            scores["Social"],
            scores["Stress"],
        )

        scores["Personality"] = ptype
        scores["ColorSector"] = pcolor
        scores["StressComment"] = self.stress_comment(scores["Stress"])
        scores["vector192"] = vector192.tolist()

        return scores

    # ------------------------------------------------------
    # 10.0 総合コメント
    # ------------------------------------------------------
    def generate_comment(self, scores: dict):
        stress = scores["Stress"]
        energy = scores["Energy"]
        fatigue = scores["Fatigue"]

        if stress > 70:
            stress_comment = "⚠ ストレス高め。休息推奨"
        elif stress > 40:
            stress_comment = "ややストレスあり"
        else:
            stress_comment = "安定状態"

        if energy > 70:
            personality = "🔥 行動型 タイプ"
        elif fatigue > 70:
            personality = "🌱 内省型 タイプ"
        elif scores["Emotion"] > 60:
            personality = "🎨 創造型 タイプ"
        else:
            personality = "🔬 分析型 タイプ"

        if scores["Arousal"] > 70:
            color = "🔴 高覚醒状態"
        elif scores["Arousal"] < 30:
            color = "🔵 低覚醒状態"
        else:
            color = "🟢 安定状態"

        return stress_comment, personality, color


    # ------------------------------------------------------
    # 10.1 女性　総合コメント
    # ------------------------------------------------------
    def generate_daily_message(self):
        messages = [
            "ゆっくりでも大丈夫です🌿",
            "今日は少しだけ、自分を大切に✨",
            "無理しない一日を過ごしましょう☕",
            "あなたのペースで大丈夫です🌸",
            "ちょっと一息ついてみましょう🌙",
        ]
        return random.choice(messages)

        
    def generate_empathy_summary(self, scores):
        if scores["Energy"] < 30:
            return "前回より少し疲れが出ていますね🌿"
        elif scores["Energy"] > 60:
            return "少し元気が戻ってきています✨"
        else:
            return "大きな変化はなさそうです☕"
            

if __name__ == "__main__":
    engine = VoiceStateEngine()
    state = engine.analyze_from_file("../static/voice_web.wav")

    print("\nVoice State\n")
    for k, v in state.items():
        print(f"{k:12} {v}")
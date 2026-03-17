# ==========================================================
# VoiceAura VoiceState Engine
# patient5/core/voice_state_engine.py
# 192 speaker embedding -> 5 Voice State
# ==========================================================

import numpy as np


class VoiceStateEngine:

    # ------------------------------------------------------
    # 1 init
    # ------------------------------------------------------
    def __init__(self):

        self.scale = 100

    # ------------------------------------------------------
    # 2 normalize
    # ------------------------------------------------------
    def _normalize(self, v):

        v = np.asarray(v, dtype=float)
#        v = np.array(v)

        norm = np.linalg.norm(v)

        if norm == 0:
            return v

        return v / norm


    # ------------------------------------------------------
    # 3 Energy
    # ------------------------------------------------------
    def _energy(self, v):

        val = np.mean(np.abs(v)) * 800

        return val


    # ------------------------------------------------------
    # 4 Stress
    # ------------------------------------------------------
    def _stress(self, v):

        val = np.std(v) * 600

        return val


    # ------------------------------------------------------
    # 5 Emotion
    # ------------------------------------------------------
    def _emotion(self, v):

        val = abs(np.mean(v)) * 1200

        return val


    # ------------------------------------------------------
    # 6 Focus
    # ------------------------------------------------------
    def _focus(self, v):

        val = (1.0 / (1.0 + np.var(v))) * 100

        return val


    # ------------------------------------------------------
    # 7 Social
    # ------------------------------------------------------
    def _social(self, v):

        val = (np.max(v) - np.min(v)) * 200

        return val


    # ------------------------------------------------------
    # 8 clamp
    # ------------------------------------------------------
    def _clamp(self, x):

        x = max(0, min(self.scale, x))

        return int(x)

    # ------------------------------------------------------
    # 8.1 追加　personality type
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
    # 8.2 追加　color sector
    # ------------------------------------------------------

    def _color_sector(self, energy, emotion, focus, social, stress):

        score = (energy + emotion + focus + social) / 4

        sectors = [

            ("#8F00FF","violet","直感・ビジョン・想像"),
            ("#001F54","navy","思考・分析"),
            ("#0077FF","blue","冷静・論理"),
            ("#00B7C2","turquoise","対人感覚"),
            ("#00A86B","emerald","会話力"),
            ("#7FFF00","lime","共感"),
            ("#FFD300","yellow","自信"),
            ("#FFD700","gold","存在感"),
            ("#FF8C00","orange","満足感"),
            ("#FF6F61","coral","身体感覚"),
            ("#FF0000","red","行動力"),
            ("#FF00FF","magenta","愛情・包容")
        ]

        idx = int(score / 100 * 11)

        color,name,desc = sectors[idx]

        return f"{name} : {desc}"


    # ------------------------------------------------------
    # 9 predict
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

        # ------------------------------
        # new metrics
        # ------------------------------

        fatigue = (100 - energy + stress) / 2
        arousal = (energy + emotion) / 2

        # ------------------------------
        # stress comment
        # ------------------------------

        stress_clamped = self._clamp(stress)

        comment = self.stress_comment(stress_clamped)

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

            "StressComment": comment
        }

    # ------------------------------------------------------
    # stress comment
    # ------------------------------------------------------

    def stress_comment(self, stress):

        stress = int(stress)

        if stress < 20:
            return "とてもリラックスした声です。穏やかで安定した精神状態です。"

        elif stress < 40:
            return "ストレスレベルは低いです。 声の調子も落ち着いていますよ。"

        elif stress < 60:
            return "中程度のストレスを検出しました。普段通りの日常的な状態です。"

        elif stress < 80:
            return "ストレス値が高まっています。メンタル負荷および疲労の懸念あり。"

        else:
            return "強いストレスを検知しました。声のトーンから、相当なプレッシャーを感じているのが伝わってきます。"


# ==========================================================
# test
# ==========================================================

if __name__ == "__main__":

    engine = VoiceStateEngine()

    vec = np.random.randn(192)

    state = engine.predict(vec)

    print("\nVoice State\n")

    for k, v in state.items():
        print(f"{k:8} {v}")
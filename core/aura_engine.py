import wave
import numpy as np
from scipy.ndimage import gaussian_filter1d


class AuraEngine:

    # =========================
    # 正規化
    # =========================
    def normalize(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float32)

        x_min = float(np.min(x))
        x_max = float(np.max(x))

        if (x_max - x_min) < 1e-8:
            return np.zeros_like(x, dtype=np.float32)

        return ((x - x_min) / (x_max - x_min)).astype(np.float32)

    # =========================
    # 🔥 完全ループ補間
    # =========================
    def interpolate(self, values: np.ndarray, resolution: int = 360) -> np.ndarray:
        values = np.asarray(values, dtype=np.float32)

        if len(values) < 2:
            return np.zeros(resolution, dtype=np.float32)

        # 🔥 ループ閉じる
        values_loop = np.concatenate([values, values[:1]])

        x_old = np.linspace(0, 1, len(values_loop))
        x_new = np.linspace(0, 1, resolution)

        interp = np.interp(x_new, x_old, values_loop)

        return interp.astype(np.float32)

    # =========================
    # VoiceDNA抽出
    # =========================
    def extract_voicedna(self, wav_path: str) -> np.ndarray:
        with wave.open(wav_path, "rb") as wf:
            audio = wf.readframes(wf.getnframes())

        audio = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0

        if len(audio) == 0:
            return np.zeros(192, dtype=np.float32)

        n = min(len(audio), 8192)

        if n < 512:
            padded = np.pad(audio, (0, 512 - n))
            spec = np.abs(np.fft.rfft(padded))
        else:
            spec = np.abs(np.fft.rfft(audio[:n]))

        spec = np.log1p(spec).astype(np.float32)

        if len(spec) < 192:
            spec = np.pad(spec, (0, 192 - len(spec)))
        else:
            spec = spec[:192]

        return self.normalize(spec)

    # =========================
    # リング生成
    # =========================
    def build_rings(
        self,
        voicedna: np.ndarray,
        sigma: float = 2.0,
        resolution: int = 360,
        psy_weight: float = 0.5,
        contrast: float = 1.0,
    ):
        # =========================
        # 内リング（DNA）
        # =========================
        dna = self.interpolate(voicedna, resolution)

        sigma = max(0.0, float(sigma))

        if sigma > 0:
            dna = gaussian_filter1d(dna, sigma=sigma * 0.2, mode='wrap')

        dna = self.normalize(dna)

        # =========================
        # 中リング（PSY）
        # =========================
        psy = np.abs(np.gradient(dna)).astype(np.float32)

        if sigma > 0:
            psy = gaussian_filter1d(psy, sigma=max(1.0, sigma * 0.5), mode='wrap')

        psy = self.normalize(psy)

        # =========================
        # 外リング（AURA）
        # =========================
        aura = (dna ** 0.7) + psy * float(psy_weight)

        if sigma > 0:
            aura = gaussian_filter1d(aura, sigma=sigma * 0.6, mode='wrap')

        aura = self.normalize(aura)

        # =========================
        # コントラスト
        # =========================
        contrast = max(0.1, float(contrast))

        dna = np.power(np.clip(dna, 0, 1), contrast * 1.8).astype(np.float32)
        psy = np.power(np.clip(psy, 0, 1), contrast * 1.0).astype(np.float32)
        aura = np.power(np.clip(aura, 0, 1), contrast * 2.0).astype(np.float32)

        dna = self.normalize(dna)
        psy = self.normalize(psy)
        aura = self.normalize(aura)

        return dna, psy, aura

    # =========================
    # メイン解析
    # =========================
    def analyze_from_file(
        self,
        wav_path: str,
        sigma: float = 2.0,
        upscale: int = 1,
        psy_weight: float = 0.5,
        contrast: float = 1.0,
    ):
        upscale = max(1, min(int(upscale), 4))
        resolution = 360 * upscale

        voicedna = self.extract_voicedna(wav_path)

        dna, psy, aura = self.build_rings(
            voicedna=voicedna,
            sigma=sigma,
            resolution=resolution,
            psy_weight=psy_weight,
            contrast=contrast,
        )

        return {
            "dna": dna.tolist(),
            "psy": psy.tolist(),
            "aura": aura.tolist(),
        }
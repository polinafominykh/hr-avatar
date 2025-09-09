from typing import Optional, List, Tuple
import time
import numpy as np
import torch
from faster_whisper import WhisperModel

# --- Silero VAD (для стримера) ---
model_vad, utils = torch.hub.load(
    repo_or_dir="snakers4/silero-vad", model="silero_vad", trust_repo=True
)
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

SR = 16000  # работаем в 16 кГц, mono, PCM16


def pcm16_to_float32(pcm16: bytes) -> np.ndarray:
    a = np.frombuffer(pcm16, dtype=np.int16)
    return a.astype(np.float32) / 32768.0


# --- ASR модель (CPU). Для стабильности лучше "base" ---
whisper = WhisperModel("small", device="cpu", compute_type="int8")


def transcribe_segment(pcm: bytes, lang: Optional[str] = "ru", bias_terms: Optional[list[str]] = None) -> str:
    if not pcm:
        return ""

    audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

    init_prompt = None
    # временно отключаем bias для борьбы с заеданием
    if bias_terms:
        # при желании включишь обратно, но держи список коротким
        pass

    segments, info = whisper.transcribe(
        audio,
        language=lang or "ru",
        vad_filter=False,
        without_timestamps=True,
        beam_size=1, best_of=1, temperature=0.0,
        compression_ratio_threshold=2.8,
        log_prob_threshold=-0.35,
        no_speech_threshold=0.8,
        condition_on_previous_text=False,
        task="transcribe",
    )

    parts = []
    for seg in segments:
        if seg.text:
            t = seg.text.strip()
            parts.append(t)
    out = " ".join(parts).strip()
    return out




class SileroStreamer:
    """
    Накопление аудио и VAD-поиск речи. Раз в ~0.5 сек пытается выделить новые
    сегменты речи и отдаёт их один раз (чтобы не дублировать).
    """
    def __init__(self, sample_rate: int = SR, min_chunk_sec: float = 0.5, lookback_sec: float = 8.0):
        self.sr = sample_rate
        self.buf = bytearray()
        self.min_emit_samples = int(min_chunk_sec * self.sr) * 2  # bytes
        self.lookback_samples = int(lookback_sec * self.sr) * 2
        self.last_end_sample = 0  # до какого места уже эмитили сегменты
        self.t0 = time.time()

    def push(self, data: bytes) -> List[Tuple[bytes, float]]:
        """
        Добавляет байты PCM16 и возвращает новые сегменты [(pcm_bytes, t_end_sec), ...]
        """
        self.buf.extend(data)

        # ограничиваем буфер «задним окном» для скорости VAD
        if len(self.buf) > self.lookback_samples:
            extra = len(self.buf) - self.lookback_samples
            self.last_end_sample = max(0, self.last_end_sample - extra)
            del self.buf[:extra]

        # если слишком мало данных — рано
        if len(self.buf) < self.min_emit_samples:
            return []

        # готовим тензор для VAD
        wav_f32 = pcm16_to_float32(bytes(self.buf))
        wav_t = torch.from_numpy(wav_f32).to(torch.float32)

        ts = get_speech_timestamps(wav_t, model_vad, sampling_rate=self.sr)
        out = []
        for seg in ts:
            start_b = seg["start"] * 2
            end_b = seg["end"] * 2
            # отдаём только новые хвосты, которые мы ещё не эмитили
            if end_b > self.last_end_sample:
                chunk = self.buf[start_b:end_b]
                t_end = time.time() - self.t0
                out.append((bytes(chunk), t_end))
                self.last_end_sample = end_b
        return out

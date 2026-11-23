"""Person B module contract: actual decoded media -> normalized text."""
import io
import os
from pathlib import Path
from functools import lru_cache
from threading import Lock
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

_ocr_lock = Lock()
_stt_lock = Lock()
MAX_AUDIO_SECONDS = 120
MAX_PIXELS = 16_000_000


class InputError(ValueError):
    pass


class AdapterUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def ocr_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR
        return RapidOCR(intra_op_num_threads=2, inter_op_num_threads=2)
    except Exception as exc:
        raise AdapterUnavailable("OCR model could not load. Install requirements-task5.txt.") from exc


def extract_image(data: bytes) -> dict:
    try:
        with Image.open(io.BytesIO(data)) as original:
            if original.format not in {"PNG", "JPEG", "WEBP"}:
                raise InputError("Use a PNG, JPEG or WebP image.")
            if original.width * original.height > MAX_PIXELS:
                raise InputError("Image exceeds the 16-megapixel limit.")
            image = ImageOps.exif_transpose(original).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise InputError("The upload is not a readable image.") from exc
    # Shipped recognition model supports Latin/Chinese; Arabic OCR is not promised.
    with _ocr_lock:
        result, elapsed = ocr_engine()(np.asarray(image))
    lines = [{"text": str(r[1]), "confidence": float(r[2])}
             for r in (result or []) if float(r[2]) >= 0.45]
    text = "\n".join(r["text"] for r in lines).strip()
    if not text:
        raise InputError("No readable text found. Try a sharper, higher-contrast image.")
    return {"text": text, "input_type": "image", "metadata": {
        "engine": "RapidOCR ONNX", "recognition_languages": "Latin/Chinese",
        "width": image.width, "height": image.height, "lines": lines,
        "confidence": sum(r["confidence"] for r in lines) / len(lines)}}


def decode_audio(data: bytes) -> np.ndarray:
    import av
    buffers = []
    count = 0
    try:
        with av.open(io.BytesIO(data)) as container:
            if not container.streams.audio:
                raise InputError("No audio stream found.")
            resampler = av.audio.resampler.AudioResampler(format="fltp", layout="mono", rate=16000)
            for frame in container.decode(audio=0):
                for f in resampler.resample(frame):
                    arr = f.to_ndarray().reshape(-1)
                    count += len(arr)
                    if count > MAX_AUDIO_SECONDS * 16000:
                        raise InputError("Audio exceeds the 120-second limit.")
                    buffers.append(arr)
            for f in resampler.resample(None):
                arr = f.to_ndarray().reshape(-1)
                count += len(arr)
                if count > MAX_AUDIO_SECONDS * 16000:
                    raise InputError("Audio exceeds the 120-second limit.")
                buffers.append(arr)
    except InputError:
        raise
    except Exception as exc:
        raise InputError("Cannot decode audio. Use WAV, MP3, M4A, OGG or WebM.") from exc
    audio = np.concatenate(buffers).astype(np.float32) if buffers else np.array([], dtype=np.float32)
    if len(audio) < 1600 or not np.isfinite(audio).all() or np.sqrt(np.mean(audio ** 2)) < 0.0001:
        raise InputError("Audio is empty or silent. Please record a spoken question.")
    return audio


@lru_cache(maxsize=1)
def speech_model():
    try:
        from faster_whisper import WhisperModel
        return WhisperModel(os.getenv("STT_MODEL", "base"), device="cpu", compute_type="int8",
                            cpu_threads=2, download_root=os.getenv("MODEL_CACHE_DIR"))
    except Exception as exc:
        raise AdapterUnavailable("Speech model could not load. First use requires a model download.") from exc


def transcribe(data: bytes) -> dict:
    audio = decode_audio(data)
    with _stt_lock:
        try:
            segments, info = speech_model().transcribe(audio, beam_size=3, temperature=0)
            text = " ".join(s.text.strip() for s in segments if s.no_speech_prob < .85).strip()
        except AdapterUnavailable:
            raise
        except Exception as exc:
            raise AdapterUnavailable("Speech recognition failed. Verify the model and audio input.") from exc
    if not text:
        raise InputError("No speech recognized. Try a clearer recording.")
    return {"text": text, "input_type": "voice", "metadata": {
        "engine": "faster-whisper", "model": Path(os.getenv("STT_MODEL", "base")).name,
        "language": info.language, "language_probability": info.language_probability,
        "duration_seconds": round(len(audio) / 16000, 3)}}

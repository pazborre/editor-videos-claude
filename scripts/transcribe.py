"""Transcribe un audio/video con Whisper local y timestamps por palabra.

Uso: python3 scripts/transcribe.py <video_o_audio> <salida.json> [idioma]
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import soundfile as sf
from faster_whisper import WhisperModel

MODEL = Path.home() / ".cache/whisper-small-ct2"

src, dst = sys.argv[1], sys.argv[2]
lang = sys.argv[3] if len(sys.argv) > 3 else None

# faster-whisper choca con la versión de PyAV instalada: le pasamos el audio ya decodificado.
with tempfile.TemporaryDirectory() as tmp:
    wav = f"{tmp}/a.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav],
                   check=True)
    audio, _ = sf.read(wav, dtype="float32")

model = WhisperModel(str(MODEL), device="cpu", compute_type="int8", cpu_threads=4)
segs, info = model.transcribe(audio, language=lang, word_timestamps=True, beam_size=5)
out = {"language": info.language, "segments": []}
for s in segs:
    out["segments"].append({
        "start": s.start, "end": s.end, "text": s.text,
        "words": [{"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)}
                  for w in s.words],
    })
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}")
json.dump(out, open(dst, "w"), ensure_ascii=False, indent=1)
print("idioma:", info.language)

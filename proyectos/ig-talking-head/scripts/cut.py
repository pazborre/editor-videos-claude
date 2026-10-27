"""Corta el video crudo: tramos elegidos, sin pausas internas, upscale a 1080x1920 30fps."""
import json, re, subprocess, sys

SRC = "media/raw.mp4"
OUT = "media/cut.mp4"
PAD = 0.09          # margen alrededor de cada palabra al cortar una pausa
MIN_SIL = 0.28      # pausas más cortas se dejan

# Pausas que no se cortan (palabras suaves que silencedetect confunde con silencio)
PROTECT = [(42.0, 42.7)]  # "los seres humanos"

# (inicio, fin) en segundos del crudo, en el orden del video final
RANGES = [
    (39.02, 43.22),  # HOOK: el rol principal ... lo tienen las personas, los seres humanos
    (0.50, 1.32),    # la gobernanza
    (3.10, 7.40),    # es poder darle un marco de acción a una política pública
    (17.64, 34.12),  # aplicado en IA ... puede ser sensible
    (49.75, 57.10),  # tener mecanismos, estándares, guías ... para no cometer errores
    (75.10, 85.30),  # trabajemos dentro de ciertos marcos ... éticamente responsable
]

log = subprocess.run(["ffmpeg", "-hide_banner", "-i", SRC, "-af",
                      f"silencedetect=n=-38dB:d={MIN_SIL}", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
silences = [(s, e) for s, e in zip(starts, ends)
            if not any(ps <= s and e <= pe for ps, pe in PROTECT)]

keeps = []
for a, b in RANGES:
    cur = a
    for s, e in silences:
        if s + PAD > a and e - PAD < b and (e - s) > MIN_SIL:
            if s + PAD > cur:
                keeps.append((cur, s + PAD))
            cur = max(cur, e - PAD)
    keeps.append((cur, b))
keeps = [(round(a, 3), round(b, 3)) for a, b in keeps if b - a > 0.12]

import os, tempfile
tmp = tempfile.mkdtemp(prefix="cut-")
listfile = os.path.join(tmp, "list.txt")
with open(listfile, "w") as lf:
    for i, (a, b) in enumerate(keeps):
        d = b - a
        seg = os.path.join(tmp, f"{i:03d}.mov")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-i", SRC, "-t", f"{d:.3f}",
                        "-vf", "fps=30,scale=1080:1920:flags=lanczos,unsharp=5:5:0.6,format=yuv420p",
                        "-af", f"afade=t=in:d=0.015,afade=t=out:st={d-0.015:.3f}:d=0.015",
                        "-c:v", "libx264", "-crf", "14", "-preset", "medium",
                        "-c:a", "pcm_s16le", "-ar", "48000", seg], check=True)
        lf.write(f"file '{seg}'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
                "-c", "copy", OUT.replace(".mp4", ".mov")], check=True)

# Mapa de cortes: dónde empieza cada tramo en la línea de tiempo final
t, cuts = 0.0, []
for a, b in keeps:
    cuts.append({"src": [a, b], "out": round(t, 3)})
    t += b - a
hook_end = sum(b - a for a, b in keeps if RANGES[0][0] <= a < RANGES[0][1])
json.dump({"cuts": cuts, "duration": round(t, 3), "hook_end": round(hook_end, 3)},
          open("media/cuts.json", "w"), indent=1)
print(f"{len(keeps)} tramos, duración final {t:.2f}s")

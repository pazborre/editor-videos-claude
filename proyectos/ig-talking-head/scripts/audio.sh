#!/usr/bin/env bash
# Limpieza de voz: graves fuera, ruido de sala, presencia, compresión, -14 LUFS (Instagram).
set -euo pipefail
cd "$(dirname "$0")/.."
CHAIN="highpass=f=85,lowpass=f=13000,afftdn=nr=12:nf=-40:tn=1,\
equalizer=f=250:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=3,equalizer=f=8000:t=q:w=1.5:g=1.5,\
acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=4,\
alimiter=limit=0.9:level=disabled"
ffmpeg -v error -y -i media/cut.mov -vn -ac 1 -ar 48000 -af "$CHAIN" media/voice_pre.wav
# loudnorm en dos pasadas para que sea lineal (sin bombeo)
M=$(ffmpeg -hide_banner -i media/voice_pre.wav -af loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$M" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -v error -y -i media/voice_pre.wav -af "loudnorm=I=-14:TP=-1.5:LRA=9:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" -ac 2 media/voice.wav
ffmpeg -hide_banner -i media/voice.wav -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:|LRA:)" | tail -3
# ajuste fino de ganancia al objetivo exacto (loudnorm lineal queda corto si choca con el techo)
I=$(ffmpeg -hide_banner -i media/voice.wav -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
ffmpeg -v error -y -i media/voice.wav -af "volume=$(python3 -c "print(round(-14-($I),2))")dB,alimiter=limit=0.84:level=disabled" media/voice_final.wav
mv media/voice_final.wav media/voice.wav
ffmpeg -hide_banner -i media/voice.wav -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)" | tail -2

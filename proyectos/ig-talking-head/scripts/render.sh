#!/usr/bin/env bash
# Renderiza la composición (video mudo + gráficos) y le suma la voz procesada.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p renders
hyperframes render --quality delivery --fps 30 -o renders/overlay.mp4 --quiet
ffmpeg -v error -y -i renders/overlay.mp4 -i media/voice.wav \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 17 -profile:v high -level 4.2 -pix_fmt yuv420p \
  -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest renders/ig-final.mp4
ffprobe -v error -show_entries format=duration,bit_rate:stream=codec_name,width,height,r_frame_rate -of compact renders/ig-final.mp4

#!/usr/bin/env bash
# Instala todo lo necesario para crear y renderizar videos en una sesión nueva
# de Claude Code en la nube. Es idempotente: lo que ya está instalado se saltea.
set -euo pipefail

HF_VERSION=0.8.209
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Solo en la nube: en una compu local no toca paquetes del sistema (forzalo con --force).
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ] && [ "${1:-}" != "--force" ]; then
  echo "setup.sh: no es una sesión en la nube, no hago nada."
  exit 0
fi

if ! dpkg -s fonts-noto-color-emoji >/dev/null 2>&1 || ! command -v convert >/dev/null || ! command -v sox >/dev/null; then
  echo "→ Paquetes del sistema (FFmpeg, fuentes, ImageMagick, SoX, libs de Chrome)"
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    ffmpeg fonts-noto fonts-noto-color-emoji fonts-liberation fonts-dejavu \
    imagemagick sox libnss3 libatk-bridge2.0-0 libgbm1 libxkbcommon0 libasound2t64 \
    libpangocairo-1.0-0 libcups2 libxcomposite1 libxdamage1 libxrandr2 >/dev/null
fi

if [ "$(hyperframes --version 2>/dev/null)" != "$HF_VERSION" ]; then
  echo "→ HyperFrames $HF_VERSION"
  npm install -g "hyperframes@$HF_VERSION" --silent
fi

echo "→ Chrome Headless Shell"
hyperframes browser ensure >/dev/null

if ! python3 -c "import kokoro_onnx, soundfile" 2>/dev/null; then
  echo "→ Kokoro (TTS local)"
  pip install -q kokoro-onnx soundfile 2>/dev/null
fi

# Dependencias de cada proyecto (solo si el repo ya está clonado).
for dir in "$REPO_DIR"/proyectos/*/; do
  if [ -f "$dir/package.json" ] && [ ! -d "$dir/node_modules" ]; then
    echo "→ npm install en $(basename "$dir")"
    (cd "$dir" && npm install --silent --no-fund --no-audit)
  fi
done

echo "✓ Entorno de video listo"

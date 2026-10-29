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

if ! command -v hyperframes >/dev/null; then  # se autoactualiza; no fijar versión acá
  echo "→ HyperFrames $HF_VERSION"
  npm install -g "hyperframes@$HF_VERSION" --silent
fi

echo "→ Chrome Headless Shell"
hyperframes browser ensure >/dev/null

if ! python3 -c "import kokoro_onnx, soundfile" 2>/dev/null; then
  echo "→ Kokoro (TTS local)"
  pip install -q kokoro-onnx soundfile 2>/dev/null
fi

if ! python3 -c "import faster_whisper" 2>/dev/null; then
  echo "→ faster-whisper (transcripción)"
  pip install -q faster-whisper 2>/dev/null
fi

# Whisper small (CTranslate2 int8). Hugging Face está bloqueado: se baja de npm en 4 partes
# con `npm pack` (sin ejecutar scripts) y se verifica el checksum.
WHISPER_DIR="$HOME/.cache/whisper-small-ct2"
WHISPER_SHA=ca732cb1379efc49417d028465f543d83a39de2c61f3027678de103dc404ce73
if [ "$(sha256sum "$WHISPER_DIR/model.bin" 2>/dev/null | cut -d' ' -f1)" != "$WHISPER_SHA" ]; then
  echo "→ Modelo Whisper small (~250 MB)"
  DL="$(mktemp -d)"
  (cd "$DL" && for i in 0 1 2 3; do
    npm pack -q "@skillninja/shortmovie-telop-model-p$i@1.0.0" >/dev/null 2>&1
    mkdir "p$i" && tar xzf "skillninja-shortmovie-telop-model-p$i-1.0.0.tgz" -C "p$i"
  done)
  mkdir -p "$WHISPER_DIR"
  cp "$DL"/p0/package/{config.json,preprocessor_config.json,tokenizer.json,vocabulary.json} "$WHISPER_DIR/"
  cat "$DL"/p0/package/model.bin.part0 "$DL"/p1/package/model.bin.part1 \
      "$DL"/p2/package/model.bin.part2 "$DL"/p3/package/model.bin.part3 > "$WHISPER_DIR/model.bin"
  rm -rf "$DL"
  if [ "$(sha256sum "$WHISPER_DIR/model.bin" | cut -d' ' -f1)" != "$WHISPER_SHA" ]; then
    echo "✗ Checksum del modelo Whisper no coincide; lo borro." >&2
    rm -f "$WHISPER_DIR/model.bin"
  fi
fi

# Dependencias de cada proyecto (solo si el repo ya está clonado).
for dir in "$REPO_DIR"/proyectos/*/; do
  if [ -f "$dir/package.json" ] && [ ! -d "$dir/node_modules" ]; then
    echo "→ npm install en $(basename "$dir")"
    (cd "$dir" && npm install --silent --no-fund --no-audit)
  fi
done

echo "✓ Entorno de video listo"

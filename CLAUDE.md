# Editor de videos

Repo de proyectos de video: HyperFrames (`proyectos/hf-demo`), Remotion (`proyectos/remotion-demo`) y FFmpeg.
Cada proyecto nuevo va en su propia carpeta dentro de `proyectos/`.

## Al empezar una sesión

Un hook SessionStart corre `scripts/setup.sh` automáticamente. Si aun así `hyperframes --version` falla o faltan `node_modules`, corrélo a mano antes de nada.

## Restricciones de red en la nube

- `cdn.jsdelivr.net` está bloqueado. En HyperFrames no cargues librerías desde CDN: instalalas con npm y
  copiá el archivo a `vendor/` (ej.: `vendor/gsap.min.js`), referenciándolo con ruta relativa.
- `remotion.media` está bloqueado. `remotion.config.ts` usa el Chrome Headless Shell de HyperFrames;
  copiá ese bloque en cada proyecto Remotion nuevo.
- npm, pip y apt funcionan.

## Reels de talking-head (flujo estándar)

Referencia: `proyectos/ig-talking-head` (scripts `cut.py`, `audio.sh`, `build.py`, `render.sh`). Para un video nuevo:

1. Copiá ese proyecto a `proyectos/<nombre>/` (sin `media/` ni `renders/`) y poné el crudo en `media/raw.mp4`.
2. Transcribí: `python3 scripts/transcribe.py media/raw.mp4 media/transcript.json es` (Whisper local en
   `~/.cache/whisper-small-ct2`, lo instala `setup.sh`).
3. Elegí hook + tramos (30–45 s salvo que se pida otra cosa) en `RANGES` de `cut.py`; mostrále el plan al usuario.
4. `cut.py` → `audio.sh` → transcribí `media/voice.wav` a `media/transcript_cut.json` → ajustá `FIX`, tarjetas y
   hook en `build.py` → `hyperframes snapshot` para revisar → `render.sh`.
5. Leé la transcripción del corte: si falta una palabra, el umbral de silencio está cortando voz (ver `PROTECT`).

Estilo: Montserrat 900, acento `#FFD23F`, subtítulos palabra por palabra, tarjetas arriba de la cabeza,
zoom alternado en cada corte, voz a -14 LUFS, 1080x1920 30 fps.

## Salidas

Los renders (`renders/`, `out/`, `*.mp4`) están en `.gitignore`. Entregá los videos con SendUserFile o
subilos a Google Drive; no los commitees.

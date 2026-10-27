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

## Salidas

Los renders (`renders/`, `out/`, `*.mp4`) están en `.gitignore`. Entregá los videos con SendUserFile o
subilos a Google Drive; no los commitees.

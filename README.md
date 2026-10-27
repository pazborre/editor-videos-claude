# Editor de videos con Claude

Proyectos de video hechos con código, para crear, editar, animar y renderizar con Claude Code.

| Herramienta | Para qué sirve |
|---|---|
| [HyperFrames](https://hyperframes.heygen.com) | Videos escritos en HTML + CSS + GSAP, renderizados a MP4 |
| [Remotion](https://www.remotion.dev) | Videos escritos en React, renderizados a MP4 |
| FFmpeg | Cortar, unir, mezclar audio, subtítulos, convertir formatos |

## Estructura

```
proyectos/
  hf-demo/         ejemplo HyperFrames (index.html)
  remotion-demo/   ejemplo Remotion (src/)
scripts/
  setup.sh         instala todo en una sesión nueva en la nube
```

Los videos renderizados (`renders/`, `out/`, `*.mp4`) no se suben al repo: descargalos o guardalos en Drive.

## Renderizar

```bash
cd proyectos/hf-demo && hyperframes render
cd proyectos/remotion-demo && npx remotion render HelloWorld out/hello.mp4
```

## Sesión nueva en la nube

Corré `bash scripts/setup.sh` (tarda ~1–3 min la primera vez). Para que sea automático, pegá su contenido en el Setup script del entorno.

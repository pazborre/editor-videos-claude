"""Genera index.html (composición HyperFrames) a partir de la transcripción del corte.

Subtítulos palabra por palabra, tarjetas de texto destacado y zooms sutiles en cada corte.
"""
import html
import json
import re
import subprocess

W, H = 1080, 1920
ACCENT = "#FFD23F"

words = [
    {"w": w["w"].strip(), "s": w["s"], "e": w["e"]}
    for seg in json.load(open("media/transcript_cut.json"))["segments"]
    for w in seg["words"]
]

# Correcciones de transcripción (Whisper oye "dar" y agrega "la" donde se cortó "pero").
FIX = {"dar": "darle", "pública": "pública.", "aplicada": "Aplicado"}
out = []
for i, w in enumerate(words):
    if w["w"] == "la" and i > 0 and words[i - 1]["w"] == "en" and words[i - 2]["w"] == "aplicada":
        continue
    w["w"] = FIX.get(w["w"], w["w"])
    out.append(w)
words = out

duration = float(subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
     "media/cut_video.mp4"], capture_output=True, text=True).stdout)
duration = round(duration - 0.02, 2)
cuts = [c["out"] for c in json.load(open("media/cuts.json"))["cuts"]]


def at(token, after=0.0):
    """Momento en que se dice la primera palabra que empieza con `token` desde `after`."""
    for w in words:
        if w["s"] >= after and re.sub(r"[^\wáéíóúñ]", "", w["w"].lower()).startswith(token):
            return w["s"]
    raise ValueError(token)


# --- Subtítulos: grupos cortos, corte en puntuación o pausas ---
chunks, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    nxt = words[i + 1] if i + 1 < len(words) else None
    text = " ".join(x["w"] for x in cur)
    if (nxt is None or re.search(r"[.,?!]$", w["w"]) or len(cur) >= 3 or len(text) >= 16
            or nxt["s"] - w["e"] > 0.35):
        chunks.append(cur)
        cur = []

# --- Tarjetas destacadas: (inicio, fin, kicker, [(texto, momento, estilo)]) ---
cards = [
    (at("gobernanza"), at("vendría") - 0.15, "Gobernanza",
     [("Un marco de acción", at("marco"), "title"), ("para la IA", at("inteligencia"), "title")]),
    (at("vendría"), at("porque") - 0.15, "Las 3 preguntas",
     [("¿Para qué?", at("qué", at("para")), "chip"), ("¿Cómo?", at("cómo"), "chip"),
      ("¿Con qué cuidados?", at("cuidados"), "chip")]),
    (at("porque"), at("tener", at("sensible")) - 0.15, "Información pública",
     [("…pero sensible", at("sensible"), "title")]),
    (at("tener", at("sensible")), at("trabajemos") - 0.15, "Para no cometer errores",
     [("Mecanismos", at("mecanismos"), "chip"), ("Estándares", at("estándares"), "chip"),
      ("Guías", at("guías"), "chip")]),
    (at("que", at("estándares", at("trabajemos"))), duration, "Usar la IA de manera",
     [("Inteligente", at("inteligente"), "title"),
      ("+ éticamente responsable", at("éticamente"), "accent")]),
]

js = []
caps_html = []
for ci, ch in enumerate(chunks):
    start = ch[0]["s"]
    end = chunks[ci + 1][0]["s"] if ci + 1 < len(chunks) else duration
    end = min(end, ch[-1]["e"] + 0.6)
    spans = "".join(f'<span class="w" id="w{ci}_{wi}">{html.escape(w["w"])}</span> '
                    for wi, w in enumerate(ch))
    caps_html.append(f'<div class="cap" id="c{ci}">{spans.strip()}</div>')
    js.append(f'tl.fromTo("#c{ci}",{{autoAlpha:0,y:26,scale:.9}},'
              f'{{autoAlpha:1,y:0,scale:1,duration:.16,ease:"back.out(2.4)"}},{start:.3f});')
    js.append(f'tl.set("#c{ci}",{{autoAlpha:0}},{end:.3f});')
    for wi, w in enumerate(ch):
        js.append(f'tl.set("#w{ci}_{wi}",{{color:"{ACCENT}",scale:1.07}},{w["s"]:.3f});')
        if wi + 1 < len(ch):
            js.append(f'tl.set("#w{ci}_{wi}",{{color:"#fff",scale:1}},{ch[wi + 1]["s"]:.3f});')

cards_html = []
for k, (a, b, kicker, items) in enumerate(cards):
    rows = []
    for j, (text, t, style) in enumerate(items):
        rows.append(f'<div class="item {style}" id="k{k}_{j}">{html.escape(text)}</div>')
        ease = '"back.out(2)"' if style == "chip" else '"power3.out"'
        js.append(f'tl.fromTo("#k{k}_{j}",{{autoAlpha:0,y:24,scale:.94}},'
                  f'{{autoAlpha:1,y:0,scale:1,duration:.38,ease:{ease}}},{t:.3f});')
    wrap = "chips" if items[0][2] == "chip" else "stack"
    cards_html.append(f'<div class="card" id="k{k}"><div class="kicker">{html.escape(kicker)}</div>'
                      f'<div class="{wrap}">{"".join(rows)}</div></div>')
    js.append(f'tl.fromTo("#k{k}",{{autoAlpha:0,y:-30}},{{autoAlpha:1,y:0,duration:.42,'
              f'ease:"power3.out"}},{a:.3f});')
    if b < duration:
        js.append(f'tl.to("#k{k}",{{autoAlpha:0,y:-18,duration:.25,ease:"power2.in"}},{b - 0.25:.3f});')

# --- Hook (antes de la primera tarjeta) ---
hook_end = cards[0][0] - 0.1
js += [
    'tl.fromTo("#hook .pill",{autoAlpha:0,y:-20},{autoAlpha:1,y:0,duration:.35,ease:"power3.out"},0.05);',
    'tl.fromTo("#hook .big",{autoAlpha:0,y:40,filter:"blur(10px)"},'
    '{autoAlpha:1,y:0,filter:"blur(0px)",duration:.5,ease:"power4.out"},0.15);',
    f'tl.fromTo("#hook .bar",{{scaleX:0}},{{scaleX:1,duration:.5,ease:"power3.inOut"}},{at("personas"):.3f});',
    f'tl.to("#hook",{{autoAlpha:0,y:-24,duration:.25,ease:"power2.in"}},{hook_end - 0.25:.3f});',
]

# --- Zoom: alterna encuadre abierto / cerrado en cada corte, con un empuje lento ---
seg_bounds = cuts + [duration]
for i in range(len(cuts)):
    a, b = seg_bounds[i], seg_bounds[i + 1]
    base = 1.0 if i % 2 == 0 else 1.1
    js.append(f'tl.set("#vwrap",{{scale:{base}}},{a:.3f});')
    js.append(f'tl.to("#vwrap",{{scale:{base + 0.035:.3f},duration:{b - a:.3f},ease:"none"}},{a:.3f});')

js.append(f'tl.to("#fade",{{autoAlpha:1,duration:.35,ease:"power1.in"}},{duration - 0.35:.3f});')

page = f"""<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="vendor/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Montserrat"; font-weight: 600; src: url("vendor/fonts/montserrat-latin-600-normal.woff2") format("woff2"); }}
      @font-face {{ font-family: "Montserrat"; font-weight: 800; src: url("vendor/fonts/montserrat-latin-800-normal.woff2") format("woff2"); }}
      @font-face {{ font-family: "Montserrat"; font-weight: 900; src: url("vendor/fonts/montserrat-latin-900-normal.woff2") format("woff2"); }}
      :root {{ --accent: {ACCENT}; --ink: #fff; --panel: rgba(12, 16, 32, 0.78); }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Montserrat", sans-serif; }}
      #vwrap {{ position: absolute; inset: 0; transform-origin: 54% 34%; will-change: transform; }}
      #v {{ width: 100%; height: 100%; object-fit: cover; filter: contrast(1.06) saturate(1.1) brightness(1.02); }}
      .shade {{ position: absolute; inset: 0; pointer-events: none;
        background: linear-gradient(180deg, rgba(0,0,0,.55) 0%, rgba(0,0,0,0) 26%, rgba(0,0,0,0) 56%, rgba(0,0,0,.5) 82%, rgba(0,0,0,.6) 100%); }}
      .vignette {{ position: absolute; inset: 0; pointer-events: none;
        background: radial-gradient(ellipse at 54% 40%, rgba(0,0,0,0) 55%, rgba(0,0,0,.35) 100%); }}

      #hook {{ position: absolute; top: 190px; left: 70px; right: 70px; text-align: center; }}
      #hook .pill {{ display: inline-block; background: var(--accent); color: #111; font-weight: 900;
        font-size: 34px; letter-spacing: .12em; padding: 12px 26px; border-radius: 999px; }}
      #hook .big {{ margin-top: 26px; color: var(--ink); font-weight: 900; font-size: 104px; line-height: 1.02;
        letter-spacing: -.02em; text-shadow: 0 6px 30px rgba(0,0,0,.55); }}
      #hook .bar {{ height: 12px; width: 420px; margin: 22px auto 0; background: var(--accent);
        border-radius: 6px; transform-origin: left center; }}

      .card {{ position: absolute; top: 170px; left: 60px; right: 60px; text-align: center; visibility: hidden; }}
      .kicker {{ display: inline-block; color: #111; background: var(--accent); font-weight: 900; font-size: 30px;
        letter-spacing: .12em; text-transform: uppercase; padding: 10px 22px; border-radius: 10px; }}
      .stack {{ margin-top: 18px; display: flex; flex-direction: column; align-items: center; gap: 6px; }}
      .stack .item {{ color: var(--ink); font-weight: 900; font-size: 82px; line-height: 1.05; letter-spacing: -.02em;
        text-shadow: 0 6px 28px rgba(0,0,0,.6); }}
      .stack .item.accent {{ color: var(--accent); font-size: 66px; }}
      .chips {{ margin-top: 22px; display: flex; flex-wrap: wrap; justify-content: center; gap: 16px; }}
      .chips .item {{ color: var(--ink); background: var(--panel); border: 3px solid rgba(255,255,255,.18);
        font-weight: 800; font-size: 52px; padding: 14px 30px; border-radius: 22px; }}
      .item {{ visibility: hidden; }}

      #captions {{ position: absolute; left: 60px; right: 60px; top: 1260px; height: 220px; }}
      .cap {{ position: absolute; inset: 0; display: flex; flex-wrap: wrap; justify-content: center; align-content: center;
        gap: 4px 34px; visibility: hidden; color: var(--ink); font-weight: 900; font-size: 76px; line-height: 1.1;
        letter-spacing: -.01em; text-align: center; }}
      .w {{ display: inline-block; -webkit-text-stroke: 10px #000; paint-order: stroke fill;
        text-shadow: 0 8px 24px rgba(0,0,0,.55); }}
      #fade {{ position: absolute; inset: 0; background: #000; visibility: hidden; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{duration}" data-width="{W}" data-height="{H}">
      <div id="vwrap">
        <video id="v" class="clip" src="media/cut_video.mp4" muted playsinline
               data-start="0" data-duration="{duration}" data-track-index="0"></video>
      </div>
      <div class="vignette"></div>
      <div class="shade"></div>
      <div id="hook"><div class="pill">IA EN EL SENADO</div><div class="big">¿Quién tiene<br>el control?</div><div class="bar"></div></div>
      {"".join(cards_html)}
      <div id="captions">{"".join(caps_html)}</div>
      <div id="fade"></div>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      " + l for l in js).strip()}
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""
open("index.html", "w").write(page)
print(f"index.html: {duration}s, {len(chunks)} subtítulos, {len(cards)} tarjetas, {len(cuts)} cortes")

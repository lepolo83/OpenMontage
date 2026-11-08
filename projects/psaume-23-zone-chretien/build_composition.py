#!/usr/bin/env python3
"""Génère hyperframes/index.html (9:16, 1080x1920) pour « Psaume 23 — Zone-Chrétien ».

Entrées : artifacts/timing.json (calage narration), assets/images/img*.jpg + credits.json (facultatif).
Usage   : python build_composition.py
"""
import html
import json
import re
from pathlib import Path

P = Path(__file__).resolve().parent
T = json.loads((P / "artifacts/timing.json").read_text(encoding="utf-8"))
CUES, TOTAL = T["cues"], float(T["total"])
HF = P / "hyperframes"
(HF / "assets").mkdir(parents=True, exist_ok=True)

NAVY, GOLD = "#0B1E3D", "#D4AF37"
INTRO_END = CUES[0]["start"]
VERSE_END = CUES[-1]["end"] + 0.9
END_START = VERSE_END
FADE = 0.8

# --- images (6 attendues) -------------------------------------------------
credits_path = P / "assets/images/credits.json"
credits = json.loads(credits_path.read_text(encoding="utf-8")) if credits_path.exists() else []
imgs = []
for i, c in enumerate(credits[:6]):
    f = c.get("file")
    if f and (P / "assets/images" / f).exists():
        author = re.sub(r"<[^>]+>", "", c.get("author") or "")
        author = html.unescape(author).strip()
        imgs.append({"src": f"assets/{f}", "author": author[:48]})
        src = P / "assets/images" / f
        dst = HF / "assets" / f
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            dst.write_bytes(src.read_bytes())

n_scenes = max(len(imgs), 1)
per = len(CUES) // n_scenes if imgs else len(CUES)
starts = [CUES[min(i * per, len(CUES) - 1)]["start"] for i in range(n_scenes)]
starts[0] = INTRO_END - 0.2
ends = starts[1:] + [VERSE_END]

scenes_html, motion_js = [], []
for i in range(n_scenes):
    s = starts[i]
    d = round(ends[i] - s + (FADE if i < n_scenes - 1 else 0.4), 2)
    track = 1 + (i % 2)
    if imgs:
        im = imgs[i]
        art = (f'<img id="bg-{i}" class="bgimg" src="{im["src"]}" alt="">'
               f'<div class="frame"><img id="img-{i}" class="photo" src="{im["src"]}" alt=""></div>'
               f'<div class="credit">{html.escape(im["author"])}</div>')
    else:
        art = '<div class="frame placeholder"></div>'
    scenes_html.append(
        f'<section id="scene-{i}" class="clip scene" data-start="{s:.2f}" data-duration="{d}" data-track-index="{track}">'
        f'<div class="veil"></div>{art}</section>')
    # mouvements de caméra doux et alternés
    zi = i % 2 == 0
    x0, x1 = (-18, 18) if i % 3 == 0 else (18, -18) if i % 3 == 1 else (0, 0)
    y0, y1 = (14, -14) if i % 3 == 2 else (0, 0)
    motion_js.append(
        f'tl.fromTo("#scene-{i}", {{opacity:0}}, {{opacity:1, duration:{FADE}, ease:"power1.inOut"}}, {s:.2f});'
        + (f'tl.to("#scene-{i}", {{opacity:0, duration:{FADE}, ease:"power1.inOut"}}, {s + d - FADE:.2f});' if i < n_scenes - 1 else "")
        + (f'tl.fromTo("#img-{i}", {{scale:{1.0 if zi else 1.14}, x:{x0}, y:{y0}}}, '
           f'{{scale:{1.14 if zi else 1.0}, x:{x1}, y:{y1}, duration:{d}, ease:"none"}}, {s:.2f});'
           f'tl.fromTo("#bg-{i}", {{scale:1.25}}, {{scale:1.35, duration:{d}, ease:"none"}}, {s:.2f});' if imgs else ""))

subs_html, subs_js = [], []
for k, c in enumerate(CUES):
    a, b = max(c["start"] - 0.12, 0), c["end"] + 0.35
    subs_html.append(
        f'<div id="sub-{k}" class="clip sub" data-start="{a:.2f}" data-duration="{b - a:.2f}" data-track-index="5">'
        f'<p>{html.escape(c["text"])}</p></div>')
    subs_js.append(
        f'tl.from("#sub-{k} p", {{opacity:0, y:18, duration:0.35, ease:"power2.out"}}, {a:.2f});'
        f'tl.to("#sub-{k} p", {{opacity:0, duration:0.25, ease:"power1.in"}}, {b - 0.25:.2f});')

doc = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080, height=1920">
<title>Psaume 23 — Zone-Chrétien</title>
<script src="assets/gsap.min.js"></script>
<style>
  :root {{ --navy:{NAVY}; --gold:{GOLD}; --ivory:#F6EFD9; }}
  html, body {{ margin:0; background:var(--navy); }}
  #root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:var(--navy);
          font-family:'Playfair Display', Georgia, serif; color:var(--ivory); }}
  .layer {{ position:absolute; inset:0; }}
  #bgfill {{ background:radial-gradient(120% 80% at 50% 30%, #17356b 0%, {NAVY} 55%, #060f20 100%); }}
  .clip {{ position:absolute; }}
  .scene {{ left:0; top:0; width:1080px; height:1920px; overflow:hidden; }}
  .veil {{ position:absolute; inset:0; background:{NAVY}; }}
  .bgimg {{ position:absolute; left:-60px; top:-60px; width:1200px; height:2040px; object-fit:cover;
           filter:blur(38px) brightness(.38) saturate(.9); }}
  .frame {{ position:absolute; left:54px; top:250px; width:972px; height:1040px; overflow:hidden;
           border:3px solid var(--gold); border-radius:6px; box-shadow:0 30px 80px rgba(0,0,0,.55); background:#08142a; }}
  .frame.placeholder {{ background:linear-gradient(160deg,#16335f,#0B1E3D); }}
  .photo {{ position:absolute; left:0; top:0; width:100%; height:100%; object-fit:cover; }}
  .credit {{ position:absolute; left:54px; top:1304px; width:972px; text-align:right; font:400 24px 'Inter', sans-serif;
            letter-spacing:.06em; color:rgba(212,175,55,.8); }}
  #topline {{ left:0; top:112px; width:1080px; text-align:center; z-index:20; }}
  #topline .k {{ font:600 30px 'Inter', sans-serif; letter-spacing:.5em; color:var(--gold); }}
  #topline .r {{ width:120px; height:2px; background:var(--gold); margin:22px auto 0; }}
  .sub {{ left:70px; top:1400px; width:940px; height:330px; z-index:30; display:flex; align-items:flex-start; justify-content:center; }}
  .sub p {{ margin:0; text-align:center; font:500 58px/1.28 'Playfair Display', Georgia, serif; color:var(--ivory);
           text-shadow:0 3px 26px rgba(0,0,0,.9); }}
  #brand {{ left:0; top:1810px; width:1080px; text-align:center; font:500 26px 'Inter', sans-serif;
           letter-spacing:.42em; color:rgba(212,175,55,.75); z-index:20; }}
  #intro {{ left:0; top:0; width:1080px; height:1920px; z-index:40; }}
  #intro .wrap {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }}
  #intro h1 {{ margin:0; font:700 150px 'Playfair Display', serif; color:var(--gold); letter-spacing:.02em; }}
  #intro .sm {{ font:500 34px 'Inter', sans-serif; letter-spacing:.4em; color:var(--ivory); margin-top:30px; }}
  #intro .bar {{ width:160px; height:3px; background:var(--gold); margin:36px 0; }}
  #end {{ left:0; top:0; width:1080px; height:1920px; z-index:50; }}
  #end .bg {{ position:absolute; inset:0; background:radial-gradient(110% 70% at 50% 40%, #17356b 0%, {NAVY} 60%, #060f20 100%); }}
  #end .wrap {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:0 90px; box-sizing:border-box; }}
  #end h2 {{ margin:0; font:700 112px/1.05 'Playfair Display', serif; color:var(--gold); }}
  #end .dash {{ font:400 70px 'Playfair Display', serif; color:var(--gold); margin:26px 0 8px; }}
  #end p {{ margin:0; font:500 50px/1.4 'Playfair Display', serif; color:var(--ivory); max-width:860px; }}
  #end .rule {{ width:220px; height:3px; background:var(--gold); margin:44px 0 0; }}
</style>
</head>
<body>
<div id="root" data-composition-id="psaume23" data-width="1080" data-height="1920" data-start="0" data-duration="{TOTAL}">
  <div id="bgfill" class="layer"></div>
  {''.join(scenes_html)}
  <div id="topline" class="clip" data-start="{INTRO_END:.2f}" data-duration="{END_START - INTRO_END:.2f}" data-track-index="6"><div class="k">PSAUME 23</div><div class="r"></div></div>
  {''.join(subs_html)}
  <div id="brand" class="clip" data-start="{INTRO_END:.2f}" data-duration="{END_START - INTRO_END:.2f}" data-track-index="7">ZONE-CHRÉTIEN</div>
  <div id="intro" class="clip" data-start="0" data-duration="{INTRO_END + 0.8:.2f}" data-track-index="8">
    <div class="wrap"><h1 id="i-h">Psaume 23</h1><div class="bar" id="i-bar"></div><div class="sm" id="i-sm">LOUIS SEGOND · 1910</div></div>
  </div>
  <div id="end" class="clip" data-start="{END_START:.2f}" data-duration="{TOTAL - END_START:.2f}" data-track-index="9">
    <div class="bg"></div>
    <div class="wrap"><h2 id="e-h">Zone-Chrétien</h2><div class="dash" id="e-d">—</div><p id="e-p">La Parole. La Louange. L'Impact.</p><div class="rule" id="e-r"></div></div>
  </div>
  <audio id="mix" src="assets/mix.wav" data-start="0" data-duration="{TOTAL}" data-track-index="20" data-volume="1"></audio>
</div>
<script>
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused: true }});
  // intro
  tl.from("#i-h", {{opacity:0, y:30, duration:1.1, ease:"power2.out"}}, 0.2);
  tl.from("#i-bar", {{scaleX:0, duration:0.9, ease:"power2.out"}}, 0.9);
  tl.from("#i-sm", {{opacity:0, duration:0.9, ease:"power1.out"}}, 1.3);
  tl.to("#intro", {{opacity:0, duration:0.8, ease:"power1.inOut"}}, {INTRO_END:.2f});
  // scènes + caméra
  {chr(10).join('  ' + m for m in motion_js)}
  // sous-titres
  {chr(10).join('  ' + m for m in subs_js)}
  // carton final
  tl.from("#end", {{opacity:0, duration:1.0, ease:"power1.inOut"}}, {END_START:.2f});
  tl.from("#e-h", {{opacity:0, y:34, duration:1.0, ease:"power2.out"}}, {END_START + 0.5:.2f});
  tl.from("#e-d", {{opacity:0, duration:0.6}}, {END_START + 1.2:.2f});
  tl.from("#e-p", {{opacity:0, y:20, duration:1.0, ease:"power2.out"}}, {END_START + 1.6:.2f});
  tl.from("#e-r", {{scaleX:0, duration:0.9, ease:"power2.out"}}, {END_START + 2.2:.2f});
  window.__timelines["psaume23"] = tl;
</script>
</body>
</html>
"""
(HF / "index.html").write_text(doc, encoding="utf-8")
(HF / "assets" / "mix.wav").write_bytes((P / "assets/audio/mix.wav").read_bytes())
print(f"index.html écrit — {n_scenes} scène(s), {len(CUES)} sous-titres, {TOTAL}s, images={len(imgs)}")

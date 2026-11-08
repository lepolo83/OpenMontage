#!/usr/bin/env python3
"""Récupère des vignettes Wikimedia Commons (domaine public / CC0) décrites par fetch/request.json."""
import json, re, sys, time, html
from pathlib import Path
import requests
from PIL import Image

UA = "OpenMontage-ZoneChretien/1.0 (https://zone-chretien.org)"
API = "https://commons.wikimedia.org/w/api.php"
PAUSE = 3.0
S = requests.Session(); S.headers["User-Agent"] = UA
_last = [0.0]

def get(url, **kw):
    for attempt in range(6):
        wait = PAUSE - (time.time() - _last[0])
        if wait > 0: time.sleep(wait)
        r = S.get(url, timeout=60, **kw); _last[0] = time.time()
        if r.status_code == 429 or r.status_code >= 500:
            ra = r.headers.get("Retry-After", "")
            delay = int(ra) if ra.isdigit() else 10 * (attempt + 1)
            print(f"  {r.status_code} -> pause {delay}s", flush=True); time.sleep(min(delay, 120)); continue
        r.raise_for_status(); return r
    raise RuntimeError(f"échec après retries: {url}")

def q(**p):
    return get(API, params={"format": "json", "action": "query", **p}).json()

def info(title_or_ids, width, **extra):
    return q(prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=width, **extra)

def clean(v): return html.unescape(re.sub(r"<[^>]+>", "", v or "")).strip()

def ok_license(meta, allowed):
    lic = clean(meta.get("LicenseShortName", {}).get("value")).lower()
    return any(lic == a or lic.startswith(a) for a in allowed), clean(meta.get("LicenseShortName", {}).get("value"))

def candidates(item, width):
    out = []
    if "title" in item:
        d = info(None, width, titles=item["title"])
        out += list(d.get("query", {}).get("pages", {}).values())
    for term in ([item["search"]] if "search" in item else []) + item.get("fallback_searches", []):
        d = info(None, width, generator="search", gsrsearch="filetype:bitmap " + term,
                 gsrnamespace=6, gsrlimit=20)
        pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
        print(f"  recherche « {term} » -> {len(pages)} résultat(s)", flush=True)
        out += pages
    return [p for p in out if p.get("imageinfo")]

def main():
    req = json.load(open("fetch/request.json", encoding="utf-8"))
    width = int(req.get("width", 1920)); allowed = req["allowed_licenses"]
    out = Path("assets_cache") / req["project"]; out.mkdir(parents=True, exist_ok=True)
    credits, used = [], set()
    for n, item in enumerate(req["images"], 1):
        print(f"[{n}/{len(req['images'])}] {item['id']}", flush=True)
        chosen = None
        for p in candidates(item, width):
            ii = p["imageinfo"][0]; meta = ii.get("extmetadata", {})
            good, lic = ok_license(meta, allowed)
            why = ("déjà utilisé" if p["title"] in used else "licence " + lic if not good else
                   "type/taille" if ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < 1000 else "")
            if why: print(f"  rejeté ({why}): {p['title']}", flush=True); continue
            chosen = (p, ii, meta, lic); break
        if not chosen: print(f"  AUCUN candidat valide pour {item['id']}"); sys.exit(1)
        p, ii, meta, lic = chosen; used.add(p["title"])
        url = ii.get("thumburl") or ii["url"]
        ext = ".png" if ii["mime"] == "image/png" else ".jpg"
        dest = out / f"{n:02d}-{item['id']}{ext}"
        dest.write_bytes(get(url).content)
        if dest.stat().st_size <= 0: print("  fichier vide"); sys.exit(1)
        with Image.open(dest) as im: im.verify()
        with Image.open(dest) as im: w, h = im.size
        credits.append({"id": item["id"], "file": dest.name, "title": p["title"],
            "author": clean(meta.get("Artist", {}).get("value")) or "Inconnu",
            "license": lic, "license_url": clean(meta.get("LicenseUrl", {}).get("value")),
            "source_url": ii.get("descriptionurl"), "image_url": url,
            "width": w, "height": h, "bytes": dest.stat().st_size})
        print(f"  OK {dest.name} {w}x{h} {lic} — {p['title']}", flush=True)
    (out / "credits.json").write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8")
    print("credits.json écrit")

main()

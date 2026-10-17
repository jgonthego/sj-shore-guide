#!/usr/bin/env python3
"""Add short factual descriptions + official links to geocoded places.
Description source order: Wikipedia summary (CC BY-SA, linked) -> official site's own meta description -> none.
Official website order: OSM website tag -> Wikidata P856 (official website) -> data/places_links.json (hand-checked).
Caches in data/cache/wiki.json. Writes data/places.json (the file build.py reads)."""
import json, re, html, time, urllib.parse, urllib.request, datetime as dt
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
UA = "sj-shore-guide/1.0 (https://github.com/jgonthego/sj-shore-guide)"
BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
WC = ROOT / "data/cache/wiki.json"
wc = json.loads(WC.read_text()) if WC.exists() else {}
DROP = {"Wildwoods Boardwalk", "Ocean City Boardwalk", "Cape May-Lewes Ferry", "Point Pleasant Beach Boardwalk", "Tuckerton Beer Company"}
NOWIKI = {"Fantasy Island Amusement Park", "Historic Smithville", "Storybook Land", "Cape May Brewing Company", "Ocean City Music Pier", "Playland's Castaway Cove", "Cattus Island County Park"}
RENAME = {"Linwood Bike Path": "George K. Francis Bikeway", "Brigantine Beach Nature Area": "North Brigantine Natural Area", "Gardner's Basin": "The Cove at Gardner's Basin"}
def get(url, ua=UA, timeout=25):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Language": "en"}), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")
def wiki(title):
    if title in wc: return wc[title]
    t = urllib.parse.quote(title.replace(" ", "_"), safe="")
    try:
        s = json.loads(get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{t}"))
        qid = s.get("wikibase_item"); site = None
        if qid:
            ent = json.loads(get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"))["entities"][qid]
            p = ent["claims"].get("P856")
            if p: site = p[0]["mainsnak"]["datavalue"]["value"]
        wc[title] = {"extract": s.get("extract"), "url": s["content_urls"]["desktop"]["page"], "title": s.get("title"), "qid": qid, "official": site, "type": s.get("type")}
    except Exception as ex:
        wc[title] = {"error": str(ex)}
    WC.write_text(json.dumps(wc, indent=1, ensure_ascii=False)); time.sleep(0.3)
    return wc[title]
def meta_desc(url):
    key = "META|" + url
    if key in wc: return wc[key]
    res = {"desc": None, "status": None}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            res["status"] = r.status; s = r.read(400000).decode("utf-8", "replace")
        m = re.search(r'<meta[^>]+(?:name|property)=["\'](?:og:)?description["\'][^>]+content=["\']([^"\']{20,400})', s, re.I) or \
            re.search(r'<meta[^>]+content=["\']([^"\']{20,400})["\'][^>]+(?:name|property)=["\'](?:og:)?description', s, re.I)
        if m: res["desc"] = html.unescape(m.group(1)).strip()
    except urllib.error.HTTPError as ex:
        res["status"] = ex.code
    except Exception as ex:
        res["status"] = str(ex)[:60]
    wc[key] = res; WC.write_text(json.dumps(wc, indent=1, ensure_ascii=False))
    return res
def first_sentences(t, n=240):
    if not t: return None
    t = re.sub(r"^[^|]{2,60}\s\|\s*(is\s)?", lambda m: "It is " if m.group(1) else "", t.strip())
    t = re.sub(r"\s*Call \(?\d{3}\)?[^.!]*[.!]", "", t)
    out = ""
    for s in re.split(r"(?<=[.!?])\s+", t.strip()):
        if len(out) + len(s) > n and out: break
        out += (" " if out else "") + s
    return out
links = json.loads((ROOT / "data/places_links.json").read_text()) if (ROOT / "data/places_links.json").exists() else {}
today = dt.date.today().isoformat()
places = []
for p in json.loads((ROOT / "data/cache/places_geo.json").read_text())["places"]:
    if p["name"] in DROP: continue
    if p["name"] in NOWIKI: p["wikipedia"] = None
    name = RENAME.get(p["name"], p["name"])
    et = p["extratags"]
    w = wiki(p["wikipedia"]) if p["wikipedia"] else (wiki(et["wikipedia"].split(":", 1)[1]) if et.get("wikipedia", "").startswith("en:") and p["name"] not in NOWIKI else None)
    if w and w.get("error"): w = None
    official = links.get(p["name"], {}).get("url") or et.get("website") or et.get("contact:website") or (w or {}).get("official")
    if official and official.startswith("http://"): official = "https://" + official[7:]
    desc, desc_src, desc_label = None, None, None
    if w and w.get("extract") and w.get("type") != "disambiguation":
        desc, desc_src, desc_label = first_sentences(w["extract"]), w["url"], "Wikipedia"
    site_status = None
    if official:
        m = meta_desc(official); site_status = m["status"]
        if not desc and m["desc"]:
            desc, desc_src, desc_label = first_sentences(m["desc"]), official, "official site"
    places.append({
        "name": name, "town": p["town"], "town_slug": p["town_slug"], "category": p["category"],
        "description": desc, "description_source": desc_src, "description_source_label": desc_label,
        "official_url": official, "official_url_status": site_status,
        "wikipedia_url": (w or {}).get("url"),
        "lat": p["lat"], "lon": p["lon"], "coords_source": "OpenStreetMap (Nominatim)", "osm_url": p["osm_url"],
        "osm_name": p["osm_name"], "opening_hours": et.get("opening_hours"), "checked": today,
    })
(ROOT / "data/places.json").write_text(json.dumps({"generated": today, "license_note": "Coordinates © OpenStreetMap contributors (ODbL). Descriptions quoted from Wikipedia (CC BY-SA 4.0) or the place's own website.", "places": places}, indent=1, ensure_ascii=False))
for x in places:
    print(f"{x['name'][:34]:34s} {str(x['official_url_status']):>4} {(x['official_url'] or '-')[:55]:55s} {x['description_source_label'] or 'NO DESC'}")
print(len(places))

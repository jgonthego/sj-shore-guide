#!/usr/bin/env python3
"""Geocode the curated things-to-do seed (data/places_seed.json) with OpenStreetMap Nominatim.
Nominatim usage policy: max 1 request/second, identifying User-Agent, results cached in
data/cache/nominatim.json (re-runs only send queries that are not cached yet).
A place is kept only if OSM has a matching feature near the stated town; misses are reported.
Writes data/cache/places_geo.json."""
import json, math, time, urllib.parse, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data/cache/nominatim.json"
UA = "sj-shore-guide/1.0 (https://github.com/jgonthego/sj-shore-guide; static site build, cached)"
cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
VIEWBOX = "-75.05,40.15,-73.95,38.88"   # Ocean + Atlantic + Cape May counties
def q(query):
    key = "PLACE|" + query
    if key in cache: return cache[key]
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": query, "format": "jsonv2", "limit": 3, "extratags": 1, "countrycodes": "us", "viewbox": VIEWBOX, "bounded": 1})
    time.sleep(1.1)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"}), timeout=30) as r:
        cache[key] = json.load(r)
    CACHE.write_text(json.dumps(cache, indent=1))
    return cache[key]
def miles(a, b, c, d):
    R = 3958.8; p1, p2 = math.radians(a), math.radians(c); dp = p2 - p1; dl = math.radians(d - b)
    return 2 * R * math.asin(math.sqrt(math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))
towns = {t["name"]: t for t in json.loads((ROOT / "data/towns.json").read_text())["towns"]}
SHORT = {"Upper Township (Strathmere)": "Upper Township"}
out, miss = [], []
for row in json.loads((ROOT / "data/places_seed.json").read_text()):
    name, town, cat, wiki = row[:4]; alt = row[4] if len(row) > 4 else None
    tn = next((t for t in towns.values() if t["name"].split(" (")[0] == town), None)
    res = q(f"{name}, {town}, New Jersey") or q(f"{name}, New Jersey")
    if not res and alt:
        res = q(f"{alt}, New Jersey") or q(alt)
    pick = None
    for r in res:
        lat, lon = float(r["lat"]), float(r["lon"])
        if tn and tn.get("geo") and miles(lat, lon, tn["geo"]["lat"], tn["geo"]["lon"]) > 9: continue
        pick = r; break
    if not pick: miss.append((name, town)); print("MISS", name, town); continue
    out.append({"name": name, "town": town, "town_slug": tn["slug"] if tn else None, "category": cat, "wikipedia": wiki,
                "lat": round(float(pick["lat"]), 5), "lon": round(float(pick["lon"]), 5),
                "osm_url": f"https://www.openstreetmap.org/{pick['osm_type']}/{pick['osm_id']}", "osm_name": pick.get("name"),
                "osm_display": pick.get("display_name"), "osm_class": f"{pick.get('category')}={pick.get('type')}",
                "extratags": pick.get("extratags") or {}})
    print("OK  ", name, "|", pick.get("name"), "|", pick.get("category"), pick.get("type"), "|", (pick.get("extratags") or {}).get("website", ""))
(ROOT / "data/cache/places_geo.json").write_text(json.dumps({"places": out, "missing": miss}, indent=1, ensure_ascii=False))
print(len(out), "found,", len(miss), "missing")

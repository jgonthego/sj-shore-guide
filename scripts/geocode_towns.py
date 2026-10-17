#!/usr/bin/env python3
"""Geocode town centres with OpenStreetMap Nominatim.
Respects the Nominatim usage policy: <=1 request/second, custom User-Agent, results cached
in data/cache/nominatim.json so each query is only ever sent once.
Writes lat/lon (+ source) into data/towns.json."""
import json, time, urllib.parse, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data/cache/nominatim.json"
UA = "sj-shore-guide/1.0 (https://github.com/jgonthego/sj-shore-guide; static site build, cached)"
cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
def geocode(q):
    if q in cache: return cache[q]
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "jsonv2", "limit": 1, "countrycodes": "us"})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    time.sleep(1.1)
    with urllib.request.urlopen(req, timeout=30) as r: res = json.load(r)
    cache[q] = res[0] if res else None
    CACHE.write_text(json.dumps(cache, indent=1))
    return cache[q]
if __name__ == "__main__":
    p = ROOT / "data/towns.json"; d = json.loads(p.read_text())
    QFIX = {"upper-township-strathmere": "Strathmere, Cape May County, New Jersey", "lower-township": "Lower Township, Cape May County, New Jersey"}
    for t in d["towns"]:
        q = QFIX.get(t["slug"]) or f"{urllib.parse.unquote(t['wikipedia'].rsplit('/',1)[1]).replace('_',' ').split(',')[0]}, {t['county']} County, New Jersey"
        r = geocode(q)
        if not r:
            r = geocode(f"{t['name']}, {t['county']} County, New Jersey")
        if r:
            t["geo"] = {"lat": round(float(r["lat"]), 5), "lon": round(float(r["lon"]), 5), "source": "OpenStreetMap Nominatim",
                        "source_url": f"https://www.openstreetmap.org/{r['osm_type']}/{r['osm_id']}", "query": q, "display_name": r["display_name"]}
        print(t["slug"], t.get("geo", {}).get("lat"), t.get("geo", {}).get("lon"), (r or {}).get("display_name", "NOT FOUND")[:70])
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")

#!/usr/bin/env python3
"""Refresh data/events.json from PUBLIC official town, county-tourism and tourism-authority calendars.

Only sources that publish machine-readable feeds or plain public HTML are used, at most a few
requests per source per run. Facebook is deliberately NOT used (login wall + its terms forbid
automated collection). Simpleview-style tourism APIs that need a page token are not used either.

Every event keeps: title, date, time, venue, town, lat/lon (venue coords from the feed when
published, otherwise the town centre), a link to the event and the source calendar.

Run weekly:  python3 scripts/fetch_events.py && python3 build.py
Hand-checked events go in data/events_manual.json (same shape); they are merged while upcoming.
"""
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "events.json"
MANUAL = ROOT / "data" / "events_manual.json"
NOMI_CACHE = ROOT / "data" / "cache" / "nominatim.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36 sj-shore-guide-events/1.0"
NOMI_UA = "sj-shore-guide/1.0 (https://github.com/jgonthego/sj-shore-guide; weekly build, cached)"
WINDOW_DAYS = 60
EXCLUDE = re.compile(
    r"\b(meeting|board of|council|commission|committee|caucus|work session|hearing|closed|closes|closure|"
    r"trash|bulk|recycl|election|budget|agenda|court|holiday - |offices?|support group|"
    r"storytime|story time|toddler|baby ?time|esl|tax prep|blood drive|aarp)\b",
    re.I,
)
TOWNS = json.loads((ROOT / "data" / "towns.json").read_text())["towns"]
BYSLUG = {t["slug"]: t for t in TOWNS}

# City / community names used by feeds -> our municipality slug
PLACE_TO_TOWN = {
    "toms river": "toms-river", "ortley beach": "toms-river", "bayville": "berkeley-township", "berkeley": "berkeley-township",
    "berkeley township": "berkeley-township", "waretown": "ocean-township", "manahawkin": "stafford-township",
    "stafford": "stafford-township", "stafford township": "stafford-township", "forked river": "lacey-township",
    "lanoka harbor": "lacey-township", "lacey": "lacey-township", "lacey township": "lacey-township", "brick": "brick-township",
    "brick township": "brick-township", "little egg harbor": "little-egg-harbor-township", "mystic island": "little-egg-harbor-township",
    "little egg harbor township": "little-egg-harbor-township", "tuckerton": "tuckerton", "west creek": "eagleswood-township",
    "eagleswood": "eagleswood-township", "beach haven": "beach-haven", "ship bottom": "ship-bottom", "surf city": "surf-city",
    "long beach township": "long-beach-township", "long beach island": "long-beach-township", "brant beach": "long-beach-township",
    "holgate": "long-beach-township", "loveladies": "long-beach-township", "north beach haven": "long-beach-township",
    "beach haven crest": "long-beach-township", "beach haven park": "long-beach-township", "haven beach": "long-beach-township",
    "point pleasant": "point-pleasant", "point pleasant borough": "point-pleasant", "point pleasant beach": "point-pleasant-beach",
    "seaside heights": "seaside-heights", "seaside park": "seaside-park", "lavallette": "lavallette", "island heights": "island-heights",
    "ocean gate": "ocean-gate", "pine beach": "pine-beach", "beachwood": "beachwood", "barnegat": "barnegat-township",
    "barnegat township": "barnegat-township", "barnegat light": "barnegat-light", "harvey cedars": "harvey-cedars",
    "mantoloking": "mantoloking", "bay head": "bay-head",
}
for t in TOWNS:
    PLACE_TO_TOWN.setdefault(t["name"].lower().split(" (")[0], t["slug"])

# Each source: id, type, label, tier ("official town" / "official tourism"), town (fixed) or town_from
SOURCES = [
    {"id": "brigantine", "type": "tribe", "base": "https://brigantinebeach.org", "town": "brigantine", "label": "City of Brigantine events calendar", "tier": "official town"},
    {"id": "stone-harbor", "type": "tribe", "base": "https://stoneharbornj.org", "town": "stone-harbor", "label": "Borough of Stone Harbor events calendar", "tier": "official town"},
    {"id": "upper-township", "type": "tribe", "base": "https://uppertownship.com", "town": "upper-township-strathmere", "label": "Upper Township events calendar", "tier": "official town"},
    {"id": "ocean-city", "type": "evogov", "base": "https://www.ocnj.us", "ids": "55,682,676", "town": "ocean-city", "label": "City of Ocean City calendar", "tier": "official town"},
    {"id": "ventnor-city", "type": "evogov", "base": "https://www.ventnorcity.org", "ids": "545,517,550,552,724,554,549", "town": "ventnor-city", "label": "Ventnor City calendar", "tier": "official town"},
    {"id": "margate-city", "type": "civicplus_rss", "base": "https://www.margate-nj.com", "town": "margate-city", "label": "Margate City calendar", "tier": "official town"},
    {"id": "linwood", "type": "linwood_asp", "url": "http://www.linwoodcity.org/main/events.asp", "town": "linwood", "label": "City of Linwood events page", "tier": "official town"},
    {"id": "visit-somers-point", "type": "tribe", "base": "https://visitsomerspoint.com", "town": "somers-point", "label": "Visit Somers Point events calendar", "tier": "official town"},
    {"id": "ocean-city-vacation", "type": "tribe", "base": "https://oceancityvacation.com", "town": "ocean-city", "label": "Ocean City Regional Chamber events calendar (oceancityvacation.com)", "tier": "tourism"},
    {"id": "ocean-county-tourism", "type": "tribe", "base": "https://oceancountytourism.com", "town_from": "venue_city", "max_pages": 8, "window": 31,
     "label": "Ocean County Tourism events calendar", "tier": "official tourism"},
    {"id": "wildwoods-tourism", "type": "wildwoods_html", "url": "https://wildwoodsnj.com/events-calendar/", "town": "wildwood",
     "label": "Greater Wildwood Tourism Authority events calendar (wildwoodsnj.com)", "tier": "official tourism"},
]


def get(url, timeout=40, headers=None):
    h = {"User-Agent": UA, "Accept": "*/*"}
    h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _tribe_time(sd, allday):
    return None if allday else dt.datetime.strptime(sd, "%Y-%m-%d %H:%M:%S").strftime("%-I:%M %p")


def tribe(cfg, start, end):
    q = urllib.parse.urlencode({"start_date": start.isoformat(), "end_date": end.isoformat(), "per_page": 50})
    url, out, pages = f"{cfg['base']}/wp-json/tribe/events/v1/events?{q}", [], 0
    while url and pages < cfg.get("max_pages", 3):
        data = json.loads(get(url)); pages += 1
        for e in data.get("events", []):
            sd = e["start_date"]
            v = e.get("venue") if isinstance(e.get("venue"), dict) else {}
            lat, lon = v.get("geo_lat"), v.get("geo_lng")
            out.append({
                "title": html.unescape(e["title"]).strip(),
                "start": sd[:10],
                "end": (e.get("end_date") or "")[:10] or None,
                "time": _tribe_time(sd, e.get("all_day") or sd.endswith("00:00:00")),
                "url": e["url"],
                "venue": html.unescape(v.get("venue", "") or ""),
                "city": html.unescape(v.get("city", "") or ""),
                "lat": float(lat) if lat not in (None, "") else None,
                "lon": float(lon) if lon not in (None, "") else None,
            })
        url = data.get("next_rest_url")
        if url: time.sleep(1)
    return out


def evogov(cfg, start, end):
    q = urllib.parse.urlencode({"selected_calendar_ids": cfg["ids"], "start_date": start.strftime("%-m/%-d/%Y"),
                                "end_date": end.strftime("%-m/%-d/%Y"), "search": "", "current_webpage": "calendar"})
    data = json.loads(get(f"{cfg['base']}/meetings/get_list?{q}", headers={"X-Requested-With": "XMLHttpRequest"}))
    out = []
    for e in data:
        if e.get("is_meeting"):
            continue
        m = re.search(r'href="([^"]+)"', e.get("detail_link", ""))
        out.append({"title": html.unescape(e["title"]).strip(), "start": e["start_date_short"],
                    "time": None if e.get("is_all_day") else (e.get("meeting_duration_time_only") or None),
                    "url": m.group(1) if m else f"{cfg['base']}/calendar", "venue": e.get("location") or ""})
    return out


def civicplus_rss(cfg, start, end):
    out = []
    for it in ET.fromstring(get(f"{cfg['base']}/RSSFeed.aspx?ModID=58&CID=All-calendar.xml")).iter("item"):
        desc = html.unescape(it.findtext("description") or "")
        m = re.search(r"Event date:</strong>\s*([^<]+)", desc)
        if not m:
            continue
        try:
            d = dt.datetime.strptime(m.group(1).strip(), "%B %d, %Y").date()
        except ValueError:
            continue
        t = re.search(r"Event Time:</strong>\s*([^<]+)", desc)
        out.append({"title": (it.findtext("title") or "").strip(), "start": d.isoformat(),
                    "time": t.group(1).strip() if t else None, "url": it.findtext("link"), "venue": ""})
    return out


def linwood_asp(cfg, start, end):
    txt = html.unescape(re.sub(r"<[^>]+>", "\n", get(cfg["url"], timeout=25)))
    out = []
    for m in re.finditer(r"([^\n]+?)\s*\((\w+ \d{1,2}, \d{4})(?: at ([^)]+))?\)\s*(?:Location:\s*([^\n]+))?", txt):
        try:
            d = dt.datetime.strptime(m.group(2), "%B %d, %Y").date()
        except ValueError:
            continue
        out.append({"title": m.group(1).strip(), "start": d.isoformat(), "time": (m.group(3) or None),
                    "url": cfg["url"], "venue": (m.group(4) or "").strip()})
    return out


def wildwoods_html(cfg, start, end):
    """wildwoodsnj.com month calendar: one row per day; multi-day events repeat per day."""
    out, seen = [], set()
    urls = [cfg["url"]]
    nxt = (start.replace(day=1) + dt.timedelta(days=32)).replace(day=1)
    if nxt <= end:
        urls.append(cfg["url"] + f"?month={nxt.month}&yr={nxt.year}")
    for i, u in enumerate(urls):
        if i: time.sleep(1)
        try:
            s = get(u)
        except Exception:
            if i: continue
            raise
        for href, title, date in re.findall(r'class="event-title" href="([^"]+)">([^<]+)</a><button data-eventdate="([^"]+)"', s):
            key = (href, date[:10])
            if key in seen:
                continue
            seen.add(key)
            t = html.unescape(title).strip()
            out.append({"title": t, "start": date[:10], "time": None, "url": html.unescape(href), "venue": ""})
    # collapse consecutive days of the same event into one entry with an end date
    out.sort(key=lambda r: (r["url"], r["start"]))
    merged = []
    for r in out:
        if merged and merged[-1]["url"] == r["url"] and \
           dt.date.fromisoformat(r["start"]) - dt.date.fromisoformat(merged[-1].get("end") or merged[-1]["start"]) == dt.timedelta(days=1):
            merged[-1]["end"] = r["start"]
        else:
            merged.append(dict(r))
    return merged


ADAPTERS = {"tribe": tribe, "evogov": evogov, "civicplus_rss": civicplus_rss, "linwood_asp": linwood_asp, "wildwoods_html": wildwoods_html}

_nomi = json.loads(NOMI_CACHE.read_text()) if NOMI_CACHE.exists() else {}


def geocode_city(city):
    """Town-centre coordinates for a community outside our town list (Nominatim, cached, 1 req/s)."""
    key = f"CITY|{city}, New Jersey"
    if key not in _nomi:
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": f"{city}, New Jersey", "format": "jsonv2", "limit": 1, "countrycodes": "us"})
        time.sleep(1.1)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": NOMI_UA}), timeout=30) as r:
                res = json.load(r)
            _nomi[key] = res[0] if res else None
            NOMI_CACHE.parent.mkdir(parents=True, exist_ok=True)
            NOMI_CACHE.write_text(json.dumps(_nomi, indent=1))
        except Exception:
            return None
    r = _nomi.get(key)
    return (round(float(r["lat"]), 5), round(float(r["lon"]), 5)) if r else None


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def place(r, cfg):
    slug = cfg.get("town")
    if cfg["id"] == "wildwoods-tourism":
        tl = r["title"].lower()
        slug = "north-wildwood" if "north wildwood" in tl else "wildwood-crest" if "crest" in tl else "west-wildwood" if "west wildwood" in tl else "wildwood"
    if cfg.get("town_from") == "venue_city":
        slug = PLACE_TO_TOWN.get((r.get("city") or "").strip().lower())
    r["town"] = slug
    r["town_name"] = BYSLUG[slug]["name"] if slug in BYSLUG else (r.get("city") or "").strip() or None
    if r.get("lat") is None or r.get("lon") is None or not (38.8 < r["lat"] < 40.3 and -75.3 < r["lon"] < -73.8):
        if slug in BYSLUG and BYSLUG[slug].get("geo"):
            r["lat"], r["lon"] = BYSLUG[slug]["geo"]["lat"], BYSLUG[slug]["geo"]["lon"]
            r["geo_precision"] = "town centre"
        elif r.get("city"):
            g = geocode_city(r["city"])
            r["lat"], r["lon"] = g if g else (None, None)
            r["geo_precision"] = "town centre" if g else None
        else:
            r["lat"] = r["lon"] = None
    else:
        r["geo_precision"] = "venue"
    return r


def main():
    today = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
    events, report = [], {}
    for cfg in SOURCES:
        end = today + dt.timedelta(days=cfg.get("window", WINDOW_DAYS))
        try:
            rows = ADAPTERS[cfg["type"]](cfg, today, end)
            kept = 0
            for r in rows:
                if EXCLUDE.search(r["title"]):
                    continue
                d = dt.date.fromisoformat(r["start"][:10])
                last = dt.date.fromisoformat(r["end"]) if r.get("end") else d
                if last < today or d > end:
                    continue
                if r.get("end") == r["start"]:
                    r["end"] = None
                place(r, cfg)
                r.update({"source_id": cfg["id"], "source_label": cfg["label"], "source_tier": cfg["tier"],
                          "source": cfg.get("base", cfg.get("url")), "fetched": today.isoformat()})
                events.append(r)
                kept += 1
            report[cfg["id"]] = {"ok": True, "raw": len(rows), "kept": kept, "label": cfg["label"], "url": cfg.get("base", cfg.get("url")), "tier": cfg["tier"]}
        except Exception as ex:
            report[cfg["id"]] = {"ok": False, "error": f"{ex.__class__.__name__}: {ex}"[:200], "label": cfg["label"], "url": cfg.get("base", cfg.get("url")), "tier": cfg["tier"]}
    if MANUAL.exists():
        for r in json.loads(MANUAL.read_text()):
            d = dt.date.fromisoformat(r["start"][:10])
            if d >= today:
                r.setdefault("source_id", "manual"); r.setdefault("source_tier", "official town")
                r.setdefault("town_name", BYSLUG.get(r["town"], {}).get("name"))
                if r.get("lat") is None and r["town"] in BYSLUG:
                    r["lat"], r["lon"], r["geo_precision"] = BYSLUG[r["town"]]["geo"]["lat"], BYSLUG[r["town"]]["geo"]["lon"], "town centre"
                events.append(r)
    if OUT.exists():  # keep last good events from sources that failed this run
        old = json.loads(OUT.read_text()).get("events", [])
        failed = {k for k, v in report.items() if not v["ok"]}
        for r in old:
            if r.get("source_id", r.get("town")) in failed and dt.date.fromisoformat((r.get("end") or r["start"])[:10]) >= today:
                r["stale"] = True
                events.append(r)
    # de-duplicate the same event listed by two calendars (prefer official town calendars)
    rank = {"official town": 0, "official tourism": 1, "tourism": 2}
    events.sort(key=lambda e: rank.get(e.get("source_tier"), 3))
    seen, deduped = set(), []
    for e in events:
        k = (norm_title(e["title"]), e["start"], e.get("town"))
        if k in seen:
            continue
        seen.add(k); deduped.append(e)
    # collapse recurring listings (same calendar, title and venue) into the next date + "more dates"
    deduped.sort(key=lambda e: (e["start"], e.get("town_name") or "", e["title"]))
    groups, collapsed = {}, []
    for e in deduped:
        k = (e.get("source_id"), norm_title(e["title"]), (e.get("venue") or "").lower())
        if k in groups:
            groups[k].setdefault("more_dates", []).append(e["start"])
            continue
        groups[k] = e; collapsed.append(e)
    deduped = collapsed
    OUT.write_text(json.dumps({"generated": today.isoformat(), "window_days": WINDOW_DAYS, "sources": report, "events": deduped}, indent=1, ensure_ascii=False))
    for k, v in report.items():
        print(f"{k:24s}", f"ok raw={v['raw']} kept={v['kept']}" if v["ok"] else "FAILED " + v["error"])
    print(f"wrote {len(deduped)} events -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())

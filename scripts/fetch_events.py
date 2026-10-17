#!/usr/bin/env python3
"""Refresh data/events.json from OFFICIAL town / tourism calendars only.

Sources are declared in SOURCES below. Each adapter returns a list of dicts:
  {town, title, start (ISO date or datetime), time, url, source, source_label}
Government meetings, office closures, trash pickups, etc. are filtered out so the
"This weekend / Upcoming" section shows community events only.

Run weekly:  python3 scripts/fetch_events.py && python3 build.py
Hand-verified events that no adapter can fetch can be added to data/events_manual.json
(same shape); they are merged in and kept if their date is still upcoming.
"""
import datetime as dt
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "events.json"
MANUAL = ROOT / "data" / "events_manual.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36 sj-shore-guide-events/1.0"
WINDOW_DAYS = 75
EXCLUDE = re.compile(
    r"\b(meeting|board|council|commission|committee|caucus|work session|hearing|closed|closes|"
    r"trash|bulk|recycl|election|budget|agenda|court|holiday - |offices?)\b",
    re.I,
)

# slug -> list of adapter configs
SOURCES = {
    "brigantine": [{"type": "tribe", "base": "https://brigantinebeach.org", "label": "City of Brigantine events calendar"}],
    "stone-harbor": [{"type": "tribe", "base": "https://stoneharbornj.org", "label": "Borough of Stone Harbor events calendar"}],
    "upper-township-strathmere": [{"type": "tribe", "base": "https://uppertownship.com", "label": "Upper Township events calendar"}],
    "ocean-city": [{"type": "evogov", "base": "https://www.ocnj.us", "ids": "55,682,676", "label": "City of Ocean City calendar"}],
    "ventnor-city": [{"type": "evogov", "base": "https://www.ventnorcity.org", "ids": "545,517,550,552,724,554,549", "label": "Ventnor City calendar"}],
    "margate-city": [{"type": "civicplus_rss", "base": "https://www.margate-nj.com", "label": "Margate City calendar"}],
    "linwood": [{"type": "linwood_asp", "url": "http://www.linwoodcity.org/main/events.asp", "label": "City of Linwood events page"}],
}


def get(url, timeout=30, headers=None):
    h = {"User-Agent": UA, "Accept": "*/*"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def tribe(cfg, start, end):
    q = urllib.parse.urlencode({"start_date": start.isoformat(), "end_date": end.isoformat(), "per_page": 50})
    data = json.loads(get(f"{cfg['base']}/wp-json/tribe/events/v1/events?{q}"))
    out = []
    for e in data.get("events", []):
        sd = e["start_date"]  # "YYYY-MM-DD HH:MM:SS"
        allday = e.get("all_day") or sd.endswith("00:00:00")
        out.append({
            "title": html.unescape(e["title"]).strip(),
            "start": sd[:10],
            "time": None if allday else dt.datetime.strptime(sd, "%Y-%m-%d %H:%M:%S").strftime("%-I:%M %p"),
            "url": e["url"],
            "venue": html.unescape((e.get("venue") or {}).get("venue", "") or "") if isinstance(e.get("venue"), dict) else "",
        })
    return out


def evogov(cfg, start, end):
    q = urllib.parse.urlencode({
        "selected_calendar_ids": cfg["ids"],
        "start_date": start.strftime("%-m/%-d/%Y"),
        "end_date": end.strftime("%-m/%-d/%Y"),
        "search": "",
        "current_webpage": "calendar",
    })
    data = json.loads(get(f"{cfg['base']}/meetings/get_list?{q}", headers={"X-Requested-With": "XMLHttpRequest"}))
    out = []
    for e in data:
        if e.get("is_meeting"):
            continue
        m = re.search(r'href="([^"]+)"', e.get("detail_link", ""))
        out.append({
            "title": html.unescape(e["title"]).strip(),
            "start": e["start_date_short"],
            "time": None if e.get("is_all_day") else (e.get("meeting_duration_time_only") or None),
            "url": m.group(1) if m else f"{cfg['base']}/calendar",
            "venue": e.get("location") or "",
        })
    return out


def civicplus_rss(cfg, start, end):
    xml = get(f"{cfg['base']}/RSSFeed.aspx?ModID=58&CID=All-calendar.xml")
    out = []
    for it in ET.fromstring(xml).iter("item"):
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
    txt = re.sub(r"<[^>]+>", "\n", get(cfg["url"]))
    txt = html.unescape(txt)
    out = []
    for m in re.finditer(r"([^\n]+?)\s*\((\w+ \d{1,2}, \d{4})(?: at ([^)]+))?\)\s*(?:Location:\s*([^\n]+))?", txt):
        try:
            d = dt.datetime.strptime(m.group(2), "%B %d, %Y").date()
        except ValueError:
            continue
        out.append({"title": m.group(1).strip(), "start": d.isoformat(), "time": (m.group(3) or None),
                    "url": cfg["url"], "venue": (m.group(4) or "").strip()})
    return out


ADAPTERS = {"tribe": tribe, "evogov": evogov, "civicplus_rss": civicplus_rss, "linwood_asp": linwood_asp}


def main():
    today = dt.date.today()
    end = today + dt.timedelta(days=WINDOW_DAYS)
    events, report = [], {}
    for slug, cfgs in SOURCES.items():
        for cfg in cfgs:
            try:
                rows = ADAPTERS[cfg["type"]](cfg, today, end)
                kept = 0
                for r in rows:
                    if EXCLUDE.search(r["title"]):
                        continue
                    d = dt.date.fromisoformat(r["start"][:10])
                    if not (today <= d <= end):
                        continue
                    r.update({"town": slug, "source_label": cfg["label"],
                              "source": cfg.get("base", cfg.get("url")), "fetched": today.isoformat()})
                    events.append(r)
                    kept += 1
                report[slug] = f"ok ({len(rows)} raw, {kept} kept)"
            except Exception as ex:  # keep going; report failures
                report[slug] = f"FAILED: {ex.__class__.__name__}: {ex}"
    if MANUAL.exists():
        for r in json.loads(MANUAL.read_text()):
            d = dt.date.fromisoformat(r["start"][:10])
            if today <= d <= end and not any(e["town"] == r["town"] and e["title"] == r["title"] and e["start"] == r["start"] for e in events):
                events.append(r)
    # keep previously-fetched events for sources that failed this run (so a flaky site doesn't wipe data)
    if OUT.exists():
        old = json.loads(OUT.read_text()).get("events", [])
        failed = {s for s, v in report.items() if v.startswith("FAILED")}
        for r in old:
            if r["town"] in failed and dt.date.fromisoformat(r["start"][:10]) >= today:
                r["stale"] = True
                events.append(r)
    events.sort(key=lambda e: (e["start"], e["town"], e["title"]))
    OUT.write_text(json.dumps({"generated": today.isoformat(), "window_days": WINDOW_DAYS,
                               "sources": report, "events": events}, indent=1))
    for k, v in report.items():
        print(f"{k:28s} {v}")
    print(f"wrote {len(events)} events -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())

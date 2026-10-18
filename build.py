#!/usr/bin/env python3
"""Static site generator for the South Jersey Shore Town Guide (v2: things-to-do first).

Reads  data/towns.json, data/events.json, data/places.json, data/realestate.json, data/site.json
Writes docs/  (GitHub Pages-ready; built in CI by .github/workflows/pages.yml)

Environment:
  BASE_PATH or PATH_PREFIX  URL prefix, e.g. "/sj-shore-guide". Default "" (root).
  SITE_URL                  Absolute origin for canonical URLs/sitemap, e.g. https://user.github.io
  FORM_ID                   Newsletter form id. When unset the signup form renders disabled.
  BUILD_DATE                Override "today" (YYYY-MM-DD).
"""
import datetime as dt
import html
import json
import math
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA, SRC, OUT = ROOT / "data", ROOT / "src", ROOT / "docs"


def load(name, default):
    p = DATA / name
    return json.loads(p.read_text()) if p.exists() else default


SITE = load("site.json", {})
TOWNDATA = load("towns.json", {"towns": []})
TOWNS = TOWNDATA["towns"]
BYSLUG = {t["slug"]: t for t in TOWNS}
EVDATA = load("events.json", {"events": [], "sources": {}})
PLACEDATA = load("places.json", {"places": []})
PLACES = PLACEDATA["places"]
REDATA = load("realestate.json", {"towns": {}})
RE = REDATA["towns"]

BASE = (os.environ.get("BASE_PATH") or os.environ.get("PATH_PREFIX") or "").strip()
BASE = ("/" + BASE.strip("/")) if BASE.strip("/") else ""
SITE_URL = (os.environ.get("SITE_URL") or SITE["default_site_url"]).rstrip("/")
FORM_ID = os.environ.get("FORM_ID", "").strip()
TODAY = dt.date.fromisoformat(os.environ["BUILD_DATE"]) if os.environ.get("BUILD_DATE") else dt.date.today()
BADGE_YEAR = TOWNDATA.get("badge_year", 2026)
COUNTIES = ["Ocean", "Atlantic", "Cape May"]
DEFAULT_ORIGIN = "linwood"
NEAR_MI = 10
SELLER_GUIDE = "https://jgonthego.github.io/sj-seller-guide/"
AI_MODE = "https://www.google.com/search"


def _end(ev):
    return dt.date.fromisoformat((ev.get("end") or ev["start"])[:10])


EVENTS = sorted([ev for ev in EVDATA.get("events", []) if _end(ev) >= TODAY], key=lambda ev: (ev["start"], ev["title"]))

e = lambda s: html.escape(str(s if s is not None else ""), quote=True)


def u(path=""):
    return f"{BASE}/{path.lstrip('/')}"


def absu(path=""):
    return SITE_URL + u(path)


def fmt_date(iso):
    return dt.date.fromisoformat(iso[:10]).strftime("%b %-d, %Y")


def money(v):
    if v is None:
        return None
    return "Free" if v == 0 else f"${v:g}"


def usd(v):
    return f"${v:,.0f}"


def miles(a, b, c, d):
    R = 3958.8
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = p2 - p1, math.radians(d - b)
    return 2 * R * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))


def ext(href, text, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<a href="{e(href)}" target="_blank" rel="noopener"{c}>{text}</a>'


def short_town(name):
    return (name or "").split(" (")[0]


# ----------------------------------------------------------------- categories
CAT_GROUPS = [
    ("festival", "Festivals & fairs"), ("music", "Music & shows"), ("halloween", "Halloween"), ("market", "Markets, food & drink"),
    ("active", "Runs, walks & outdoors"), ("kids", "Kids & family"), ("arts", "Arts & classes"),
    ("boardwalk", "Boardwalks & piers"), ("rides", "Rides, water parks & animals"), ("nature", "Nature & parks"),
    ("history", "Lighthouses & history"), ("drinks", "Wineries & breweries"), ("other", "Other"),
]
CAT_LABEL = dict(CAT_GROUPS)
PLACE_CAT = {"boardwalk": "boardwalk", "pier": "boardwalk", "waterfront": "boardwalk", "shopping-village": "boardwalk",
             "amusement": "rides", "water-park": "rides", "mini-golf": "rides", "aquarium": "rides", "zoo": "rides",
             "nature": "nature", "trail": "nature", "beach-spot": "nature",
             "lighthouse": "history", "history": "history", "landmark": "history", "museum": "history",
             "winery": "drinks", "brewery": "drinks", "venue": "music"}
PLACE_KIND = {"boardwalk": "Boardwalk / promenade", "pier": "Fishing pier", "waterfront": "Waterfront", "shopping-village": "Shopping street / village",
              "amusement": "Amusement park", "water-park": "Water park", "mini-golf": "Mini golf", "aquarium": "Aquarium", "zoo": "Zoo",
              "nature": "Nature spot", "trail": "Bike path / trail", "beach-spot": "Beach spot", "lighthouse": "Lighthouse",
              "history": "Historic site", "landmark": "Landmark", "museum": "Museum / gallery", "winery": "Winery", "brewery": "Brewery",
              "venue": "Venue / arena"}
EV_RULES = [
    ("halloween", r"hallowe|trunk.or.treat|trick.or|haunt|spook|\bboo\b|boos\b|monster|ghost|scarecrow|pumpkin|jacks? ?& ?lights|zombie|witch"),
    ("market", r"market|craft show|vendor|food truck|street eats|chili|oktoberfest|brews|beer|wine|tasting|dinner|\btea\b|eats|harvestfest"),
    ("active", r"\brun\b|5k|10k|\bwalk\b|race|tournament|golf|surf|paddle|yoga|bike|fun run|marathon|regatta|fishing|cleanup|sweep"),
    ("music", r"concert|music|band|tenor|jazz|orchestra|singing|\bshow\b|theat|comedy|dance|night of|tribute|oldies|doo.?wop|movie|film"),
    ("festival", r"festival|\bfest\b|\bfair\b|parade|celebrat|\bdays\b|expo|reunion|bonfire|fireworks|harvest"),
    ("kids", r"\bkids?\b|child|family|youth|teen|tween|ages \d|toddler|santa|story"),
    ("arts", r"\bart\b|\barts\b|class|workshop|paint|drawing|watercolor|glass|craft|gallery|plein|collage|exhibit|lecture|histor"),
    ("nature", r"nature|bird|refuge|garden|\bpark\b|beach|wildlife|hike|trail"),
]


def ev_cat(ev):
    t = ev["title"].lower()
    for cat, rx in EV_RULES:
        if re.search(rx, t):
            return cat
    return "other"


# ----------------------------------------------------------------- icons & art (inline SVG)
def _svg(path):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{path}</svg>'


S = 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
ICON = {
    "badge": _svg(f'<rect x="4" y="7" width="16" height="10" rx="2" {S}/><circle cx="9" cy="12" r="2" fill="currentColor"/><path d="M13 10.5h4M13 13.5h3" {S}/>'),
    "free": _svg(f'<circle cx="12" cy="12" r="8.5" {S}/><path d="M8 12.5l2.6 2.6L16 9.6" {S}/>'),
    "guard": _svg(f'<path d="M7 21V9h10v12M5 9h14l-2-5H7zM7 14h10" {S}/>'),
    "dog": _svg(f'<path d="M6 10l-2-4 4 1 2-2h4l2 2 4-1-2 4v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4z" {S}/><circle cx="10" cy="12" r="1" fill="currentColor"/><circle cx="14" cy="12" r="1" fill="currentColor"/>'),
    "alcohol": _svg(f'<path d="M7 3h10l-1 7a4 4 0 0 1-8 0zM12 14v6M8.5 21h7M4 4l16 16" {S}/>'),
    "parking": _svg(f'<rect x="4" y="4" width="16" height="16" rx="4" {S}/><path d="M10 17V7h3a3 3 0 0 1 0 6h-3" {S}/>'),
    "boardwalk": _svg(f'<path d="M3 14h18M3 18h18M6 14v6M12 14v6M18 14v6M5 14l3-6h8l3 6" {S}/>'),
    "link": _svg(f'<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" {S}/>'),
    "cal": _svg(f'<rect x="3.5" y="5" width="17" height="15" rx="3" {S}/><path d="M3.5 10h17M8 3v4M16 3v4" {S}/>'),
    "pin": _svg(f'<path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z" {S}/><circle cx="12" cy="10" r="2.2" fill="currentColor"/>'),
    "cart": _svg(f'<path d="M3 4h2l2.2 10.5a2 2 0 0 0 2 1.5h7.6a2 2 0 0 0 2-1.6L20 8H6.2" {S}/><circle cx="10" cy="20" r="1.4" fill="currentColor"/><circle cx="17" cy="20" r="1.4" fill="currentColor"/>'),
    "car": _svg(f'<path d="M4 16v-4l2-5h12l2 5v4zM7 16v3H4v-3M20 16v3h-3v-3" {S}/><circle cx="8" cy="13" r="1.2" fill="currentColor"/><circle cx="16" cy="13" r="1.2" fill="currentColor"/>'),
    "house": _svg(f'<path d="M3 11l9-7 9 7M5 10v10h14V10M10 20v-6h4v6" {S}/>'),
}

LOGO = ('<svg class="logo" viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="22" fill="#ffd23f" stroke="#111" stroke-width="3"/>'
        '<path d="M8 30c4 0 4-3 8-3s4 3 8 3 4-3 8-3 4 3 8 3v2a16 16 0 0 1-32 0z" fill="#00c2d1" stroke="#111" stroke-width="3" stroke-linejoin="round"/>'
        '<circle cx="24" cy="18" r="6" fill="#ff3d8b" stroke="#111" stroke-width="3"/></svg>')


def _wheel():
    parts = ['<svg class="wheel" viewBox="0 0 200 210" aria-hidden="true"><path d="M100 100 L58 206 M100 100 L142 206" stroke="#fff" stroke-width="6" stroke-linecap="round"/><g class="wheel-spin" fill="none">',
             '<circle cx="100" cy="100" r="78" stroke="#ff3d8b" stroke-width="6"/><circle cx="100" cy="100" r="52" stroke="#00e5ff" stroke-width="4"/>']
    cols = ["ff3d8b", "00e5ff", "ffd23f", "7cff6b"]
    for i, a in enumerate(range(0, 360, 30)):
        x, y = 100 + 78 * math.cos(math.radians(a)), 100 + 78 * math.sin(math.radians(a))
        parts.append(f'<line x1="100" y1="100" x2="{x:.1f}" y2="{y:.1f}" stroke="#ffd23f" stroke-width="3"/>'
                     f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="#{cols[i % 4]}" stroke="#111" stroke-width="3"/>')
    parts.append('<circle cx="100" cy="100" r="12" fill="#ffd23f" stroke="#111" stroke-width="3"/></g></svg>')
    return "".join(parts)


WHEEL = _wheel()
# slug -> [lat, lon, short name], used client-side by assets/weather.js to pick the weather location
TOWNS_GEO_JSON = json.dumps({t["slug"]: [t["geo"]["lat"], t["geo"]["lon"], short_town(t["name"])] for t in TOWNS if t.get("geo")},
                            separators=(",", ":")).replace("</", "<\\/")
WAVES = ('<svg class="waves" viewBox="0 0 1440 120" preserveAspectRatio="none" aria-hidden="true">'
         '<path d="M0 60 C 120 20 240 100 360 60 S 600 20 720 60 S 960 100 1080 60 S 1320 20 1440 60 V120 H0Z" fill="#00c2d1" stroke="#111" stroke-width="4"/>'
         '<path d="M0 88 C 120 58 240 118 360 88 S 600 58 720 88 S 960 118 1080 88 S 1320 58 1440 88 V120 H0Z" fill="#fff4dc"/></svg>')
STATUS_LABEL = {"verified": "Fully verified", "partial": "Partly verified", "reported": "News-reported only", "stub": "Not yet verified"}

# ----------------------------------------------------------------- explorer items
PITEMS = [{**p, "type": "place", "group": PLACE_CAT.get(p["category"], "other")} for p in PLACES]
EITEMS = [{**ev, "type": "event", "group": ev_cat(ev)} for ev in EVENTS]


def near(lat, lon, items, radius=NEAR_MI):
    res = []
    for it in items:
        if it.get("lat") is None:
            continue
        d = miles(lat, lon, it["lat"], it["lon"])
        if d <= radius:
            res.append((d, it))
    return res


# ----------------------------------------------------------------- layout
NAV = [("", "Home"), ("things-to-do/", "Things to do"), ("events/", "Events"), ("towns/", "Towns"),
       ("beach-tags/", "Beach tags"), ("buying/", "Buying at the shore"), ("about/", "About")]
PAGES = []


def ask_ai(variant="hero"):
    return f"""<form class="askai askai-{variant}" action="{AI_MODE}" method="get" target="_blank" data-askai>
  <input type="hidden" name="udm" value="50">
  <label class="askai-label" for="askai-{variant}">Ask Google AI about the shore</label>
  <div class="askai-row"><input id="askai-{variant}" name="q" type="search" required placeholder="e.g. rainy-day ideas near Cape May" autocomplete="off">
  <button type="submit" class="btn btn-ink">Ask Google AI <span aria-hidden="true">↗</span></button></div>
  <p class="askai-note">Opens Google AI Mode in a new tab and adds “South Jersey shore” to your question. Google's answers aren't checked by us.</p>
</form>"""


def footer():
    marquee = "BOARDWALKS ★ LIGHTHOUSES ★ WATER PARKS ★ FESTIVALS ★ BREWERIES ★ BIRDING ★ BONFIRES ★ MINI GOLF ★ SUNSETS ★ "
    return f"""<footer class="footer">
  <div class="marquee" aria-hidden="true"><div><span>{marquee}</span><span>{marquee}</span></div></div>
  <div class="wrap footer-grid">
    <div>
      <a class="brand brand-foot" href="{u()}">{LOGO}<span><strong>South Jersey Shore Town Guide</strong><small>Ocean · Atlantic · Cape May</small></span></a>
      <p class="small">Independent guide. Not affiliated with any town, county, tourism authority, venue or the State of New Jersey.</p>
    </div>
    <div>
      <h3>The fine print</h3>
      <p class="small">Events, rules, prices and hours change. Every fact links to the source we checked and the date we checked it. Confirm before you go. If we couldn't verify something, it says <em>Not yet verified</em>. Distances are approximate straight-line miles, not driving routes. Real-estate figures are public statistics, not appraisals or listings, and nothing here is legal or tax advice.</p>
    </div>
    <div>
      <h3>Explore</h3>
      <ul class="footlinks">
        <li><a href="{u('things-to-do/')}">Things to do</a></li><li><a href="{u('events/')}">Events</a></li>
        <li><a href="{u('towns/')}">All towns</a></li><li><a href="{u('beach-tags/')}">Beach tags &amp; rules</a></li>
        <li><a href="{u('buying/')}">Buying at the shore</a></li><li><a href="{u('buying/checklist/')}">NJ buyer checklist</a></li>
        <li><a href="{u('map/')}">County map</a></li><li><a href="{u('about/')}">About &amp; sources</a></li><li><a href="{u('sitemap.xml')}">Sitemap</a></li>
      </ul>
    </div>
  </div>
  <div class="wrap small foot-bottom">Built {TODAY.isoformat()} · Events refreshed {fmt_date(EVDATA.get('generated', TODAY.isoformat()))} · Map data © OpenStreetMap contributors · Live weather from the <a href="https://www.weather.gov/documentation/services-web-api" rel="noopener">National Weather Service</a> (public domain; not endorsed by NOAA/NWS) · No ads, no cookies, no cross-site tracking · anonymous visit counts via GoatCounter</div>
</footer>"""


def page(path, title, desc, body, *, active="", jsonld=None):
    canonical = absu(path)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>' if jsonld else ""
    navhtml = "".join(f'<a href="{u(p)}"{" aria-current=page" if active == p else ""}>{n}</a>' for p, n in NAV)
    full_title = title if title.startswith(SITE["site_name"]) else f"{title} · {SITE['site_name']}"
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canonical)}">
<meta name="theme-color" content="#060a13">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['site_name'])}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:image" content="{e(absu('assets/og.svg'))}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{u('assets/favicon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{u('assets/style.css')}">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
  <div class="wrap topbar-in">
    <a class="brand" href="{u()}">{LOGO}<span><strong>South Jersey Shore Town Guide</strong><small>Ocean · Atlantic · Cape May</small></span></a>
    <button class="navtoggle" aria-expanded="false" aria-controls="nav">Menu</button>
    <nav id="nav" class="nav">{navhtml}</nav>
  </div>
</header>
<main id="main">
{body}
</main>
{footer()}
<script type="application/json" id="sj-towns">{TOWNS_GEO_JSON}</script>
<script src="{u('assets/app.js')}" defer></script>
<script src="{u('assets/weather.js')}" defer></script>
<script>window.goatcounter={{path:function(){{return location.pathname||'/'}}}}</script>
<script data-goatcounter="https://jgonthego.goatcounter.com/count" async src="{u('assets/gc.js')}"></script>
</body>
</html>"""
    dest = OUT / path / "index.html" if (path.endswith("/") or path == "") else OUT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc)
    PAGES.append(path)


# ----------------------------------------------------------------- beach-rule helpers (unchanged logic from v1)
def prices(t):
    return t["facts"].get("prices")


def seasonal_display(t):
    p = prices(t)
    if p:
        if p.get("free_note"):
            return p["free_note"], "official"
        if p.get("seasonal") is not None:
            return money(p["seasonal"]), "official"
    pr = t["facts"].get("prices_reported")
    if pr and pr.get("seasonal"):
        return money(pr["seasonal"]), "news"
    if t["compare"].get("free_beach") is True:
        return "Free", "official"
    return None, None


def dogs_label(t):
    c = t["compare"]
    s = c.get("dogs_summer")
    if s is None:
        return "Not yet verified"
    if s == "no":
        return "Off-season only" if c.get("dogs_offseason") else "No (summer)"
    return {"limited hours": "Summer: limited hours", "dog beach": "Summer: dog beach only"}.get(s, s)


def dog_friendly(t):
    return t["compare"].get("dogs_summer") in ("limited hours", "dog beach")


def status_pill(t):
    st = t["status"]
    return f'<span class="pill pill-{st}">{STATUS_LABEL[st]}</span>'


def source_line(f):
    tier = f.get("tier", "official")
    tier_html = {"official": '<span class="tier tier-off">Official</span>', "official tourism": '<span class="tier tier-tour">Official tourism</span>',
                 "news": '<span class="tier tier-news">News report</span>'}.get(tier, "")
    return (f'<p class="src">{tier_html} Source: {ext(f["source"], e(f.get("source_label") or f["source"]))}'
            f' · <span class="checked">Last checked {fmt_date(f["checked"])}</span></p>')


def not_verified(t, what):
    off = t.get("official_url")
    link = f' Check the {ext(off, "official town website")}.' if off else ""
    return f'<p class="nv"><span class="nv-tag">Not yet verified</span> We haven\'t verified {e(what)} for {e(t["name"])} yet.{link}</p>'


def town_link(slug, name=None):
    if slug in BYSLUG:
        return f'<a href="{u("towns/" + slug + "/")}">{e(name or short_town(BYSLUG[slug]["name"]))}</a>'
    return e(name or "")


# ----------------------------------------------------------------- cards
def dist_span(d):
    return f'<span class="dist" data-dist>{"≈ %.0f mi" % d if d is not None else ""}</span>'


def event_card(ev, dist=None):
    d = dt.date.fromisoformat(ev["start"][:10])
    end = ev.get("end")
    when = d.strftime("%a, %b %-d")
    if end and end != ev["start"]:
        when += " – " + dt.date.fromisoformat(end).strftime("%a, %b %-d")
    if ev.get("time"):
        when += f" · {ev['time']}"
    more = ev.get("more_dates") or []
    more_html = f'<span class="more" title="{e(", ".join(more))}">+{len(more)} more date{"s" if len(more) > 1 else ""}</span>' if more else ""
    venue = f'<span class="ev-venue">{ICON["pin"]}{e(ev["venue"])}</span>' if ev.get("venue") else ""
    town = f'<span class="ev-town">{town_link(ev.get("town"), short_town(ev.get("town_name")))}</span>' if ev.get("town_name") else ""
    stale = '<span class="tier tier-news">may be outdated</span>' if ev.get("stale") else ""
    approx = ' <span class="muted">· distance from town centre</span>' if ev.get("geo_precision") == "town centre" else ""
    lat = ev.get("lat") if ev.get("lat") is not None else ""
    lon = ev.get("lon") if ev.get("lon") is not None else ""
    attrs = f'data-type="event" data-cat="{ev["group"]}" data-start="{ev["start"][:10]}" data-end="{(end or ev["start"])[:10]}" data-lat="{lat}" data-lon="{lon}"'
    return f"""<article class="card ev" {attrs}>
  <div class="ev-date"><span class="ev-m">{d.strftime('%b')}</span><span class="ev-d">{d.day}</span><span class="ev-w">{d.strftime('%a')}</span></div>
  <div class="ev-body">
    <p class="kicker"><span class="tag tag-{ev['group']}">{e(CAT_LABEL[ev['group']])}</span>{dist_span(dist)}</p>
    <h3>{ext(ev['url'], e(ev['title']))}</h3>
    <p class="ev-meta">{town}<span>{e(when)}</span>{more_html}{venue}{stale}</p>
    <p class="src small">Source: {ext(ev['url'], e(ev.get('source_label', 'official calendar')))} · fetched {fmt_date(ev.get('fetched', TODAY.isoformat()))}{approx}</p>
  </div>
</article>"""


def place_card(p, dist=None):
    if p.get("description"):
        desc = f'<p class="pdesc">{e(p["description"])}</p><p class="src small">Description quoted from {ext(p["description_source"], e(p["description_source_label"]))}</p>'
    else:
        desc = '<p class="pdesc nvp">No description verified yet. See the official site.</p>'
    links = []
    if p.get("official_url"):
        links.append(ext(p["official_url"], "Official site ↗", "plink"))
    if p.get("wikipedia_url"):
        links.append(ext(p["wikipedia_url"], "Wikipedia", "plink plink-soft"))
    links.append(ext(p["osm_url"], "Map", "plink plink-soft"))
    attrs = f'data-type="place" data-cat="{p["group"]}" data-lat="{p["lat"]}" data-lon="{p["lon"]}"'
    return f"""<article class="card place" {attrs}>
  <p class="kicker"><span class="tag tag-{p['group']}">{e(PLACE_KIND.get(p['category'], 'Place'))}</span>{dist_span(dist)}</p>
  <h3>{e(p['name'])}</h3>
  <p class="ptown">{ICON['pin']}{town_link(p.get('town_slug'), p['town'])}</p>
  {desc}
  <div class="plinks">{''.join(links)}</div>
  <p class="src small">Location: {ext(p['osm_url'], 'OpenStreetMap')} · checked {fmt_date(p['checked'])}</p>
</article>"""


def origin_options(selected=DEFAULT_ORIGIN):
    opts = []
    for c in COUNTIES:
        ts = sorted([t for t in TOWNS if t["county"] == c and t.get("geo")], key=lambda t: t["name"])
        o = "".join(f'<option value="{t["slug"]}" data-lat="{t["geo"]["lat"]}" data-lon="{t["geo"]["lon"]}"{" selected" if t["slug"] == selected else ""}>{e(short_town(t["name"]))}</option>' for t in ts)
        opts.append(f'<optgroup label="{e(c)} County">{o}</optgroup>')
    return "".join(opts)


def explorer(kind="both", limit=24, events_title="What's going on"):
    """Distance / category / weekend filter. kind: both | events | places. Cards are server-rendered (default: 30 mi from Linwood)."""
    groups = set()
    if kind in ("both", "events"):
        groups |= {it["group"] for it in EITEMS}
    if kind in ("both", "places"):
        groups |= {it["group"] for it in PITEMS}
    chips = "".join(f'<button type="button" class="chip-btn" data-cat="{g}" aria-pressed="false">{e(lbl)}</button>' for g, lbl in CAT_GROUPS if g in groups)
    radius = "".join(f'<button type="button" class="rad" data-r="{r}" aria-pressed="{"true" if r == 30 else "false"}">{str(r) + " mi" if r else "Any"}</button>' for r in (10, 20, 30, 45, 60, 0))
    o = BYSLUG[DEFAULT_ORIGIN]["geo"]
    secs = []
    if kind in ("both", "events"):
        cards = "".join(event_card(x, miles(o["lat"], o["lon"], x["lat"], x["lon"]) if x.get("lat") is not None else None) for x in EITEMS)
        secs.append(f"""<section class="xsec" data-sec="event">
  <div class="sec-h"><h2>{e(events_title)}</h2><p class="xcount" data-count></p></div>
  <div class="cards evlist" data-list data-limit="{limit}">{cards}</div>
  <p class="empty" data-empty hidden>Nothing on the calendars we track inside that circle. Go bigger.</p>
  <button type="button" class="btn btn-ghost more-btn" data-more hidden>Show more</button>
</section>""")
    if kind in ("both", "places"):
        pls = sorted(PITEMS, key=lambda x: miles(o["lat"], o["lon"], x["lat"], x["lon"]))
        cards = "".join(place_card(x, miles(o["lat"], o["lon"], x["lat"], x["lon"])) for x in pls)
        secs.append(f"""<section class="xsec" data-sec="place">
  <div class="sec-h"><h2>Things to do</h2><p class="xcount" data-count></p></div>
  <div class="cards plist" data-list data-limit="{limit}">{cards}</div>
  <p class="empty" data-empty hidden>Nothing from our list inside that circle yet. Go bigger.</p>
  <button type="button" class="btn btn-ghost more-btn" data-more hidden>Show more</button>
</section>""")
    weekend = "" if kind == "places" else '<button type="button" class="toggle-wk" data-weekend aria-pressed="false">★ This weekend</button>'
    return f"""<div class="explorer" data-explorer data-kind="{kind}" id="explore">
  <div class="xpanel">
    <div class="xrow xtop">
      <p class="xq">{ICON['car']} How far do you want to drive?</p>
      <div class="xorigin">
        <label for="xfrom-{kind}">From</label>
        <select id="xfrom-{kind}" data-origin>{origin_options()}<option value="geo">📍 Use my location</option></select>
        <span class="geo-status small" data-geostatus aria-live="polite"></span>
      </div>
    </div>
    <div class="xrow radius" role="group" aria-label="Distance">{radius}</div>
    <div class="xrow chips" role="group" aria-label="Categories"><button type="button" class="chip-btn on" data-cat="" aria-pressed="true">Everything</button>{chips}{weekend}</div>
    <p class="xnote small">Distances are <strong>approx. miles, straight-line</strong> (as the gull flies), not driving routes or times.</p>
  </div>
  {''.join(secs)}
</div>"""


def sponsor(kind="business"):
    if kind == "agent":
        title, text = "Featured local agent", "Your shore real-estate business here. Placeholder only: no agent or brokerage is featured, endorsed or paying for this spot."
    else:
        if not SITE["sponsor"]["enabled"]:
            return ""
        title, text = "Featured local business", "Your South Jersey business here. " + SITE["sponsor"]["text"]
    return f"""<aside class="sponsor" aria-label="{title} (placeholder)">
  <div class="sticker sticker-tilt">AD SPOT</div>
  <div><p class="sponsor-tag">{title} · <strong>PLACEHOLDER</strong></p><p class="small">{e(text)}</p></div>
</aside>"""


def signup():
    if FORM_ID:
        action = SITE["form_endpoint_template"].replace("{FORM_ID}", FORM_ID)
        form = f"""<form class="signup-form" action="{e(action)}" method="post">
  <label class="sr" for="em">Email</label><input id="em" type="email" name="email" required placeholder="you@example.com">
  <button class="btn btn-sun" type="submit">Get the weekend list</button></form>"""
    else:
        form = """<form class="signup-form is-disabled" onsubmit="return false" aria-disabled="true">
  <label class="sr" for="em">Email</label><input id="em" type="email" disabled placeholder="Signup coming soon">
  <button class="btn btn-sun" type="button" disabled>Coming soon</button></form>
  <p class="small">Placeholder: email signup is off until a form provider is configured.</p>"""
    return f"""<section class="signup"><div class="wrap signup-in">
  <div><h2>The Thursday shore list</h2><p>What's going on this weekend, straight from official calendars. No spam, no fluff.</p></div>
  <div>{form}</div></div></section>"""


def phero(title, lead, sticker=None):
    st = f'<span class="sticker sticker-hero">{e(sticker)}</span>' if sticker else ""
    return f'<section class="phero"><div class="wrap">{st}<h1>{title}</h1><p class="lead">{lead}</p></div>{WAVES}</section>'


def filters_bar(target, toggles=("free", "dog", "verified", "ocean")):
    lbl = {"free": "Free beach", "dog": "Dog friendly", "verified": "Rules verified", "ocean": "Ocean beaches"}
    tg = "".join(f'<button class="fbtn toggle" data-toggle="{k}" aria-pressed="false">{lbl[k]}</button>' for k in toggles)
    return f"""<div class="filters" data-target="{target}">
  <label class="search"><span class="sr">Search towns</span><input type="search" placeholder="Search a town…" data-f="q"></label>
  <div class="fgroup" role="group" aria-label="County"><button class="fbtn on" data-county="">All counties</button>{''.join(f'<button class="fbtn" data-county="{e(c)}">{e(c)}</button>' for c in COUNTIES)}</div>
  <div class="fgroup" role="group" aria-label="Filters">{tg}</div>
  <p class="fcount small" aria-live="polite"></p>
</div>"""


def weekend_range(today):
    wd = today.weekday()
    if wd >= 5:
        return today, today + dt.timedelta(days=6 - wd)
    s = today + dt.timedelta(days=4 - wd)
    return s, s + dt.timedelta(days=2)


# ----------------------------------------------------------------- pages: home, things, events, towns
def n_sources():
    return sum(1 for v in EVDATA.get("sources", {}).values() if v.get("ok")) + (1 if any(ev.get("source_id") == "manual" for ev in EVENTS) else 0)


def build_home():
    ws, we = weekend_range(TODAY)
    n_wk = sum(1 for ev in EITEMS if dt.date.fromisoformat(ev["start"]) <= we and _end(ev) >= ws)
    body = f"""
<section class="hero" data-wx-hero>
  {WHEEL}
  <div class="wrap hero-in">
    <p class="eyebrow"><span class="sticker">Down the shore</span> Ocean · Atlantic · Cape May</p>
    <h1><span class="neon">What's going on</span> <span class="neon neon-pink">at the shore?</span></h1>
    <p class="wx-chip" data-wxchip hidden></p>
    <p class="lead">Festivals, boardwalks, lighthouses, breweries, bonfires and what's happening this weekend near you. Pulled from official calendars, with every listing sourced. No made-up stuff.</p>
    {ask_ai('hero')}
    <ul class="stats">
      <li><strong>{len(EITEMS)}</strong><span>upcoming events</span></li>
      <li><strong>{n_wk}</strong><span>this weekend</span></li>
      <li><strong>{len(PITEMS)}</strong><span>things to do</span></li>
      <li><strong>{n_sources()}</strong><span>official calendars</span></li>
    </ul>
  </div>
  {WAVES}
</section>
<div class="wrap">
  {explorer('both', limit=9)}
  {sponsor()}
  <section class="sec promo-grid">
    <a class="promo promo-tags" href="{u('beach-tags/')}"><span class="sticker">The fine print</span><h2>Beach tags &amp; rules</h2><p>{BADGE_YEAR} badge prices, free beaches, dogs and lifeguards, all sourced. It's off-season, so most towns won't check tags until June.</p></a>
    <a class="promo promo-buy" href="{u('buying/')}"><span class="sticker sticker-pink">New</span><h2>Buying at the shore</h2><p>Median home values, 2025 tax rates, flood maps and an NJ buyer checklist for all {len(TOWNS)} towns.</p></a>
    <a class="promo promo-map" href="{u('map/')}"><span class="sticker sticker-green">Map</span><h2>All {len(TOWNS)} towns</h2><p>Point Pleasant Beach to Cape May Point, plus the bay towns. Where's the action?</p></a>
  </section>
</div>
{signup()}"""
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE["site_name"], "url": absu(), "description": SITE["tagline"]}
    page("", f"{SITE['site_name']}: things to do & events down the shore",
         f"What's going on at the South Jersey shore: {len(EITEMS)} upcoming events and {len(PITEMS)} things to do in Ocean, Atlantic and Cape May counties, filterable by distance from your town.",
         body, jsonld=ld)


def build_things():
    body = phero("Things to do down the shore", f"{len(PITEMS)} boardwalks, piers, lighthouses, water parks, nature spots, wineries and breweries. Every one is pinned on OpenStreetMap and linked to an official site where one exists. Filter by how far you'll drive.", "No filler") + \
        f'<div class="wrap">{ask_ai("page")}{explorer("places", limit=24)}<p class="small muted">Not listed? We only add places we can find on OpenStreetMap near the stated town. Restaurants and bars aren\'t listed yet.</p></div>'
    page("things-to-do/", "Things to do at the South Jersey shore", f"{len(PITEMS)} attractions, boardwalks, lighthouses, parks, wineries and breweries in Ocean, Atlantic and Cape May counties, with official links and a distance filter.", body, active="things-to-do/")


def build_events():
    srcs = EVDATA.get("sources", {})
    rows = "".join(f'<li>{"✅" if v.get("ok") else "⚠️"} {ext(v["url"], e(v["label"]))} <span class="muted">({e(v["tier"])}{", " + str(v["kept"]) + " kept" if v.get("ok") else ", fetch failed this run, last good data kept"})</span></li>' for v in srcs.values())
    manual = sum(1 for ev in EVENTS if ev.get("source_id") == "manual")
    body = phero("What's on: shore events", f"{len(EITEMS)} upcoming events from {n_sources()} official town, county-tourism and tourism-authority calendars. Refreshed every Thursday. Last refresh: {fmt_date(EVDATA.get('generated', TODAY.isoformat()))}. Meetings and closures are filtered out.", "Fresh weekly") + \
        f"""<div class="wrap">{explorer("events", limit=30, events_title="Events")}
<details class="srcdetails"><summary>Calendars we pull from ({len(srcs)}{" + " + str(manual) + " hand-checked" if manual else ""})</summary><ul class="small">{rows}</ul>
<p class="small">Categories are tagged automatically from event titles, so treat them as a rough guide. Repeat listings show the next date plus "more dates".</p>
<p class="small"><strong>Why no Facebook events?</strong> Facebook events sit behind a login, and Facebook's terms don't allow automated collection, so we don't scrape them. If an event is only on a public Facebook post, it can be added by hand once it's checked against the organizer's page.</p></details></div>"""
    page("events/", "Upcoming events at the South Jersey shore", "Upcoming festivals, concerts, markets and family events in South Jersey shore towns from official calendars, filterable by distance and weekend.", body, active="events/")


def town_card(t):
    lat, lon = t["geo"]["lat"], t["geo"]["lon"]
    n_p, n_e = len(near(lat, lon, PITEMS)), len(near(lat, lon, EITEMS))
    chips = []
    if t["compare"].get("free_beach") is True:
        chips.append('<span class="chip chip-free">Free beach</span>')
    if dog_friendly(t):
        chips.append('<span class="chip chip-dog">Dogs OK (limited)</span>')
    if t["kind"] == "bay":
        chips.append('<span class="chip chip-bay">Bay / mainland</span>')
    data = (f'data-county="{e(t["county"])}" data-free="{1 if t["compare"].get("free_beach") else 0}" data-dog="{1 if dog_friendly(t) else 0}" '
            f'data-status="{t["status"]}" data-kind="{t["kind"]}" data-name="{e(t["name"].lower())}"')
    return f"""<a class="card town-card" href="{u('towns/' + t['slug'] + '/')}" {data}>
  <span class="county">{e(t['county'])} County</span>
  <h3>{e(t['name'])}</h3>
  <div class="tc-stats"><span><strong>{n_p}</strong> things to do</span><span><strong>{n_e}</strong> events</span></div>
  <p class="small muted">within {NEAR_MI} mi</p>
  <div class="chips">{''.join(chips)}</div>
</a>"""


def build_towns_index():
    body = phero("Pick a town", f"{len(TOWNS)} shore and bay towns in Ocean, Atlantic and Cape May counties. Each town page leads with things to do and events nearby, then beach rules and a buying snapshot.", f"{len(TOWNS)} towns") + \
        f'<div class="wrap sec">{filters_bar("#all-cards")}<div class="cards" id="all-cards">{"".join(town_card(t) for t in TOWNS)}</div></div>'
    page("towns/", "All South Jersey shore towns", "Directory of South Jersey shore and bay towns: things to do, events, beach rules and buying snapshots.", body, active="towns/")


FIELD_ORDER = [
    ("badge", "Beach badge / tag", "badge", "the beach badge requirement"),
    ("free_beach", "Free beach?", "free", "free-beach status"),
    ("lifeguards", "Lifeguard season & hours", "guard", "lifeguard season and hours"),
    ("dogs", "Dogs on beach & boardwalk", "dog", "dog rules"),
    ("alcohol", "Alcohol rules", "alcohol", "alcohol rules"),
    ("parking", "Parking", "parking", "parking meters, apps or rates"),
    ("boardwalk", "Boardwalk / promenade", "boardwalk", "boardwalk/promenade details"),
]


def price_block(t):
    p, pr = prices(t), t["facts"].get("prices_reported")
    if not p and not pr:
        return ""
    if p:
        if p.get("free_note"):
            nx, nxt = p.get("next_year"), ""
            if nx:
                nxt = (f'<div class="nextyear"><strong>{nx["year"]} prices already announced:</strong> daily {money(nx["daily"])}, weekly {money(nx["weekly"])}, '
                       f'seasonal {money(nx["seasonal"])} (preseason {money(nx["preseason"])}). {ext(nx["source"], "Source")}</div>')
            return f'<div class="prices"><div class="pbox pbox-free"><span>{BADGE_YEAR}</span><strong>FREE</strong><em>no tags</em></div></div>{nxt}'
        boxes = []
        for k, lbl in (("daily", "Daily"), ("three_day", "3-day"), ("weekly", "Weekly"), ("seasonal", "Seasonal"), ("preseason", "Preseason")):
            if k in p:
                v = p.get(k)
                boxes.append(f'<div class="pbox"><span>{lbl}</span><strong>{e(money(v)) if v is not None else "—"}</strong><em>{"not published" if v is None else ""}</em></div>')
        notes = " ".join(e(p[k]) for k in ("preseason_note", "weekly_note", "missing_note", "conflict_note") if p.get(k))
        src = f'<p class="src"><span class="tier tier-off">Official</span> Prices: {ext(p["source"], e(p["source_label"]))} · <span class="checked">Last checked {fmt_date(p["checked"])}</span></p>'
        return f'<div class="price-head">{BADGE_YEAR} season prices</div><div class="prices">{"".join(boxes)}</div><p class="small muted">{notes}</p>{src}'
    boxes = "".join(f'<div class="pbox pbox-news"><span>{lbl}</span><strong>{e(money(pr.get(k))) if pr.get(k) else "—"}</strong></div>' for k, lbl in (("daily", "Daily"), ("weekly", "Weekly"), ("seasonal", "Seasonal")))
    return (f'<div class="price-head">{BADGE_YEAR} prices as reported by news media</div><div class="prices">{boxes}</div>'
            f'<p class="src"><span class="tier tier-news">News report</span> {ext(pr["source"], e(pr["source_label"]))} · <span class="checked">Last checked {fmt_date(pr["checked"])}</span>. Not yet confirmed with the town.</p>')


def fact_cards(t):
    f = t["facts"]
    cards = []
    for key, label, icon, what in FIELD_ORDER:
        if key == "badge":
            if f.get("badge"):
                b = f["badge"]
                inner = f'<p class="fv">{e(b["value"])}</p>' + (f'<p class="fd">{e(b["detail"])}</p>' if b.get("detail") else "") + source_line(b)
            elif f.get("badge_reported"):
                b = f["badge_reported"]
                inner = f'<p class="fv">{e(b["value"])}</p>' + source_line(b) + not_verified(t, "the badge rules with the town itself")
            else:
                inner = not_verified(t, what)
            inner += price_block(t)
            wb = f.get("where_to_buy")
            if wb:
                inner += f'<div class="wtb"><h4>{ICON["cart"]} Where to buy</h4><p>{e(wb["value"])}</p>{source_line(wb)}</div>'
            elif t["kind"] == "ocean":
                inner += f'<div class="wtb"><h4>{ICON["cart"]} Where to buy</h4>{not_verified(t, "where to buy tags")}</div>'
        else:
            v = f.get(key)
            inner = (f'<p class="fv">{e(v["value"])}</p>' + (f'<p class="fd">{e(v["detail"])}</p>' if v.get("detail") else "") + source_line(v)) if v else not_verified(t, what)
        ok = bool(f.get(key)) or (key == "badge" and f.get("badge_reported"))
        cards.append(f'<section class="fact {"" if ok else "fact-nv"} {"fact-wide" if key == "badge" else ""}"><h3>{ICON[icon]}{label}</h3>{inner}</section>')
    if f.get("beach_access"):
        v = f["beach_access"]
        cards.append(f'<section class="fact"><h3>{ICON["pin"]}Beach access</h3><p class="fv">{e(v["value"])}</p>{source_line(v)}</section>')
    return "".join(cards)


# ----------------------------------------------------------------- real estate
def re_snapshot(t):
    r = RE.get(t["slug"])
    if not r:
        return f'<p class="nv"><span class="nv-tag">Not yet verified</span> No public buying data loaded for {e(t["name"])} yet.</p>'
    rows = []
    mv, tx, rt = r.get("median_home_value"), r.get("tax"), r.get("ratio")
    if mv:
        val = "$2,000,000+" if mv["topcoded"] else usd(mv["value"])
        moe = "" if mv["topcoded"] or not mv.get("moe") else f' ± {usd(mv["moe"])}'
        rows.append(f'<div class="re-k"><span>Median home value</span><strong>{val}</strong><em>Owner-occupied homes, ACS {e(mv["year"])} 5-year estimate{moe}. {ext(mv["source"], "Census table B25077")}</em></div>')
    else:
        rows.append('<div class="re-k"><span>Median home value</span><strong class="nvs">Not yet verified</strong></div>')
    if tx:
        rows.append(f'<div class="re-k"><span>2025 general tax rate</span><strong>{tx["general_rate"]:.3f}</strong><em>per $100 of <u>assessed</u> value (used for bills). {ext(tx["source"], "NJ Division of Taxation")}</em></div>')
        rows.append(f'<div class="re-k"><span>2025 effective tax rate</span><strong>{tx["effective_rate"]:.3f}</strong><em>per $100 of market value, for comparing towns.</em></div>')
    if rt:
        rows.append(f'<div class="re-k"><span>Equalization ratio (tax year 2025)</span><strong>{rt["average_ratio"]:.2f}%</strong><em>average assessed ÷ true value. {ext(rt["source"], "Table of Equalized Valuations")}</em></div>')
    if mv and tx and not mv["topcoded"]:
        est = mv["value"] * tx["effective_rate"] / 100
        rows.append(f'<div class="re-k re-est"><span>Illustration: yearly tax on a median-value home</span><strong>≈ {usd(round(est, -2))}</strong><em>median value × effective rate. A rough estimate; real bills depend on the assessment.</em></div>')
    links = (f'<div class="plinks">{ext(r["flood_map"]["url"], "FEMA flood map ↗", "plink")}{ext("https://flooddisclosure.nj.gov/", "NJ flood-risk lookup ↗", "plink")}'
             f'{ext(r["search_links"]["realtor"], "Listings on Realtor.com ↗", "plink plink-soft")}{ext(r["search_links"]["zillow"], "Listings on Zillow ↗", "plink plink-soft")}'
             f'{ext(SELLER_GUIDE, "NJ closing costs (seller guide) ↗", "plink plink-soft")}</div>')
    return f"""<div class="re-grid">{''.join(rows)}</div>{links}
<p class="small muted">Last checked {fmt_date(r['checked'])}. Public statistics, not an appraisal. We don't show listings or listing photos; the search links open Realtor.com or Zillow. Read the <a href="{u('buying/checklist/')}">NJ buyer checklist</a>.</p>"""


def build_town(t):
    lat, lon = t["geo"]["lat"], t["geo"]["lon"]
    places = sorted(near(lat, lon, PITEMS), key=lambda x: x[0])
    evs = sorted(near(lat, lon, EITEMS), key=lambda x: (x[1]["start"], x[0]))
    in_town = [x for x in evs if x[1].get("town") == t["slug"]]
    name = short_town(t["name"])
    ph = "".join(place_card(it, d) for d, it in places[:12]) or f'<p class="empty">Nothing from our list within {NEAR_MI} mi yet. <a href="{u("things-to-do/")}">Browse everything →</a></p>'
    eh = "".join(event_card(it, d) for d, it in evs[:12])
    if not eh:
        eh = f'<p class="empty">No upcoming events within {NEAR_MI} mi on the calendars we track.' + (f' {ext(t["events_calendar_url"], "Check the official calendar →")}' if t.get("events_calendar_url") else "") + "</p>"
    more_ev = f'<p class="small"><a href="{u("events/")}">+{len(evs) - 12} more nearby: see all events →</a></p>' if len(evs) > 12 else ""
    links = []
    if t.get("official_url"):
        links.append(ext(t["official_url"], f'{ICON["link"]}Official town website', "lbtn"))
    if t.get("tourism_url"):
        links.append(ext(t["tourism_url"], f'{ICON["link"]}Official tourism site', "lbtn"))
    if t.get("events_calendar_url"):
        links.append(ext(t["events_calendar_url"], f'{ICON["cal"]}Official events calendar', "lbtn"))
    if t.get("facebook_url"):
        links.append(ext(t["facebook_url"], f'{ICON["link"]}More on Facebook', "lbtn lbtn-soft"))
    links.append(ext(t["wikipedia"], f'{ICON["link"]}Wikipedia', "lbtn lbtn-soft"))
    missing = [x for x, k in (("official tourism site", "tourism_url"), ("official events calendar", "events_calendar_url")) if not t.get(k)]
    ml = (f'<p class="small muted">Not yet verified: {e(", ".join(missing))}.' + (f' Start from the {ext(t["official_url"], "official town website")}.' if t.get("official_url") else "") + "</p>") if missing else ""
    notes = "".join(f"<li>{e(n)}</li>" for n in t.get("notes", []))
    notes_html = f'<details class="notes"><summary>Notes &amp; source discrepancies</summary><ul>{notes}</ul></details>' if notes else ""
    others = sorted([x for x in TOWNS if x["slug"] != t["slug"]], key=lambda x: miles(lat, lon, x["geo"]["lat"], x["geo"]["lon"]))[:10]
    nearby = "".join(f'<a class="mini" href="{u("towns/" + x["slug"] + "/")}">{e(short_town(x["name"]))} <span>≈{miles(lat, lon, x["geo"]["lat"], x["geo"]["lon"]):.0f} mi</span></a>' for x in others)
    stickers = [f'<span class="sticker">{len(places)} things to do</span>', f'<span class="sticker sticker-pink">{len(evs)} events nearby</span>']
    if t["compare"].get("free_beach") is True:
        stickers.append('<span class="sticker sticker-green">Free beach</span>')
    kind = "Ocean-beach town" if t["kind"] == "ocean" else "Bayfront / mainland town"
    stub_note = ""
    if t["status"] in ("stub", "reported"):
        stub_note = (f'<div class="stubnote"><strong>Beach rules not verified yet.</strong> {"Prices below are news-reported only. " if t["status"] == "reported" else ""}'
                     f'{"Use the official town website for current rules." if t.get("official_url") else ""}</div>')
    desc = f"{t['name']} ({t['county']} County, NJ): things to do, upcoming events nearby, beach rules ({BADGE_YEAR}) and a home-buying snapshot, with sources."
    ld = {"@context": "https://schema.org", "@type": "TouristDestination", "name": f"{t['name']}, New Jersey", "url": absu(f"towns/{t['slug']}/"),
          "geo": {"@type": "GeoCoordinates", "latitude": lat, "longitude": lon},
          "containedInPlace": {"@type": "AdministrativeArea", "name": f"{t['county']} County, New Jersey"}}
    if t.get("official_url"):
        ld["sameAs"] = [t["official_url"], t["wikipedia"]]
    body = f"""
<section class="thero">
  <div class="wrap">
    <nav class="crumbs small"><a href="{u()}">Home</a> / <a href="{u('towns/')}">Towns</a> / <span>{e(t['county'])} County</span></nav>
    <p class="county">{e(t['county'])} County · {kind}</p>
    <h1>{e(t['name'])}</h1>
    <div class="stickers">{''.join(stickers)}</div>
    <nav class="jump"><a href="#todo">Things to do</a><a href="#events">Events</a><a href="#beach">Beach rules</a><a href="#buying">Buying</a><a href="#links">Links</a></nav>
  </div>
  {WAVES}
</section>
<div class="wrap town-body">
  <section class="sec" id="todo"><div class="sec-h"><h2>Things to do in &amp; near {e(name)}</h2><a href="{u('things-to-do/')}">Everything →</a></div>
    <p class="small muted">Within {NEAR_MI} mi of the town centre, closest first (approx. straight-line miles).</p>
    <div class="cards plist">{ph}</div></section>
  <section class="sec" id="events"><div class="sec-h"><h2>What's on nearby</h2><a href="{u('events/')}">All events →</a></div>
    <p class="small muted">{len(in_town)} in {e(name)}, {len(evs) - len(in_town)} more within {NEAR_MI} mi. Soonest first.</p>
    <div class="cards evlist">{eh}</div>{more_ev}</section>
  {sponsor()}
  <section class="sec beach-sec" id="beach"><div class="sec-h"><h2>Beach rules &amp; tags <span class="muted">({BADGE_YEAR} season)</span></h2>{status_pill(t)}</div>
    {stub_note}
    <div class="facts">{fact_cards(t)}</div>
    <p class="small"><a href="{u('beach-tags/')}">Compare beach tags across all towns →</a></p></section>
  <section class="sec" id="buying"><div class="sec-h"><h2>{ICON['house']} Buying in {e(name)}</h2><a href="{u('buying/')}">All towns →</a></div>
    {re_snapshot(t)}{sponsor('agent')}</section>
  <section class="links-sec" id="links"><h2>Official links</h2><div class="lbtns">{''.join(links)}</div>{ml}</section>
  {notes_html}
  <section class="sec"><h2>Nearby towns</h2><div class="minis">{nearby}</div></section>
  <p class="small muted">Town list source: {ext(t['list_source'], 'Wikipedia: Jersey Shore § Beaches' if t['kind'] == 'ocean' else 'Wikipedia: ' + e(t['county']) + ' County municipalities')}. Town centre: {ext(t['geo']['source_url'], 'OpenStreetMap')}.</p>
</div>"""
    page(f"towns/{t['slug']}/", f"{t['name']}: things to do, events & beach rules", desc, body, active="towns/", jsonld=ld)


def compare_table():
    trs = []
    for t in TOWNS:
        price, tier = seasonal_display(t)
        p = prices(t) or {}
        daily = money(p.get("daily")) if p.get("daily") is not None else None
        pr_cell = (f'{e(price)}{"<sup>*</sup>" if tier == "news" else ""}' if price else '<span class="nvs">Not yet verified</span>')
        sortv = 9999 if not price else (0 if price.startswith("Free") else float(price.strip("$").split()[0]) if price.startswith("$") else 9998)
        fb = t["compare"].get("free_beach")
        fbcell = {True: '<span class="yes">Yes</span>', False: '<span class="no">No</span>'}.get(fb, '<span class="nvs">Not yet verified</span>')
        dl = dogs_label(t)
        dcls = "yes" if dog_friendly(t) else ("nvs" if dl == "Not yet verified" else "meh")
        wb = t["facts"].get("where_to_buy")
        trs.append(f"""<tr data-county="{e(t['county'])}" data-free="{1 if fb else 0}" data-dog="{1 if dog_friendly(t) else 0}" data-status="{t['status']}" data-kind="{t['kind']}" data-name="{e(t['name'].lower())}">
<td data-v="{e(t['name'])}"><a href="{u('towns/' + t['slug'] + '/#beach')}">{e(t['name'])}</a></td>
<td data-v="{COUNTIES.index(t['county'])}">{e(t['county'])}</td>
<td data-v="{sortv}">{pr_cell}</td>
<td data-v="{p.get('daily') if p.get('daily') is not None else 9999}">{e(daily) if daily else '<span class="nvs">—</span>'}</td>
<td data-v="{ {True: 0, False: 1}.get(fb, 2) }">{fbcell}</td>
<td data-v="{dl}"><span class="{dcls}">{e(dl)}</span></td>
<td data-v="{e(wb['value'][:30]) if wb else 'zzz'}" class="small wtbcell">{e(wb['value']) if wb else '<span class="nvs">Not yet verified</span>'}</td>
<td data-v="{list(STATUS_LABEL).index(t['status'])}">{status_pill(t)}</td>
</tr>""")
    return f"""<div class="table-wrap"><table class="cmp sortable">
<thead><tr><th>Town</th><th>County</th><th>Seasonal tag ({BADGE_YEAR})</th><th>Daily</th><th>Free beach</th><th>Dogs on beach</th><th>Where to buy</th><th>Status</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table></div>
<p class="small muted">* = price reported by news media (Patch, April 2026), not yet confirmed with the town. In-season price shown; most towns sold cheaper preseason tags until late spring. "Dogs on beach" means the summer season unless noted.</p>"""


def build_beach_tags():
    n_free = sum(t["compare"].get("free_beach") is True for t in TOWNS)
    body = phero("Beach tags &amp; rules", f"The fine print: {BADGE_YEAR} badge prices, free beaches ({n_free} of them), dog rules and where to buy for all {len(TOWNS)} towns. Click a column to sort.", f"{BADGE_YEAR} prices") + \
        f"""<div class="wrap sec">
<div class="season-note" role="note"><strong>Off-season ({TODAY.strftime('%B %Y')}):</strong> {e(SITE['season_note'])}</div>
{filters_bar('#cmp-table tbody')}<div id="cmp-table">{compare_table()}</div>
<p class="small">Each town name links to its full beach-rules section (lifeguards, alcohol, parking, boardwalk), with sources and last-checked dates.</p></div>"""
    page("beach-tags/", f"Beach tag prices & rules ({BADGE_YEAR})", f"Compare {BADGE_YEAR} beach tag prices, free beaches, dog rules and where to buy across South Jersey shore towns.", body, active="beach-tags/")
    target = u("beach-tags/")
    redirect = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved: Beach tags</title><link rel="canonical" href="{e(absu("beach-tags/"))}">'
                f'<meta http-equiv="refresh" content="0; url={e(target)}"><meta name="robots" content="noindex"></head>'
                f'<body><p>This page moved to <a href="{e(target)}">Beach tags &amp; rules</a>.</p></body></html>')
    (OUT / "compare").mkdir(parents=True, exist_ok=True)
    (OUT / "compare" / "index.html").write_text(redirect)


def build_buying():
    trs = []
    for t in TOWNS:
        r = RE.get(t["slug"], {})
        mv, tx, rt = r.get("median_home_value"), r.get("tax"), r.get("ratio")
        mvs = ("$2M+" if mv["topcoded"] else usd(mv["value"])) if mv else "—"
        estv = round(mv["value"] * tx["effective_rate"] / 100, -2) if mv and tx and not mv["topcoded"] else None
        lk = f'{ext(r["flood_map"]["url"], "FEMA")} · {ext(r["search_links"]["realtor"], "Realtor.com")} · {ext(r["search_links"]["zillow"], "Zillow")}' if r else ""
        trs.append(f"""<tr data-county="{e(t['county'])}" data-name="{e(t['name'].lower())}" data-free="0" data-dog="0" data-status="{t['status']}" data-kind="{t['kind']}">
<td data-v="{e(t['name'])}"><a href="{u('towns/' + t['slug'] + '/#buying')}">{e(t['name'])}</a></td><td data-v="{COUNTIES.index(t['county'])}">{e(t['county'])}</td>
<td data-v="{mv['value'] if mv else 0}">{mvs}</td>
<td data-v="{tx['general_rate'] if tx else 99}">{f"{tx['general_rate']:.3f}" if tx else '—'}</td>
<td data-v="{tx['effective_rate'] if tx else 99}">{f"{tx['effective_rate']:.3f}" if tx else '—'}</td>
<td data-v="{rt['average_ratio'] if rt else 0}">{f"{rt['average_ratio']:.2f}%" if rt else '—'}</td>
<td data-v="{estv or 0}">{usd(estv) if estv else '—'}</td>
<td class="small">{lk}</td></tr>""")
    n_acs = sum(1 for v in RE.values() if v.get("median_home_value"))
    body = phero("Buying at the shore", f"A public-data snapshot for {len(TOWNS)} shore and bay towns: Census median home values, 2025 NJ property-tax rates, equalization ratios, flood-map links and an NJ buyer checklist. No listings, no hype.", "Public data only") + \
        f"""<div class="wrap sec">
<div class="promo-grid">
  <a class="promo promo-buy" href="{u('buying/checklist/')}"><span class="sticker">Checklist</span><h2>NJ buyer checklist</h2><p>Attorney review, flood disclosure, flood insurance, smoke/CO certificate, rental registration.</p></a>
  <a class="promo promo-tags" href="{e(SELLER_GUIDE)}" target="_blank" rel="noopener"><span class="sticker sticker-pink">Costs</span><h2>NJ closing costs ↗</h2><p>The South Jersey seller guide covers NJ closing-cost information.</p></a>
</div>
<h2 class="h-sec">Town-by-town snapshot</h2>
{filters_bar('#re-table tbody', toggles=("ocean",))}
<div id="re-table"><div class="table-wrap"><table class="cmp sortable">
<thead><tr><th>Town</th><th>County</th><th>Median home value (ACS 2020–24)</th><th>2025 general rate</th><th>2025 effective rate</th><th>Ratio (TY 2025)</th><th>Illustrative yearly tax on median home</th><th>Links</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table></div></div>
<div class="prose small">
<h3>How to read this</h3>
<ul>
<li><strong>Median home value</strong>: U.S. Census Bureau American Community Survey 2020–2024 5-year estimates, table B25077 (owner-occupied units), by municipality ({n_acs}/{len(TOWNS)} towns). Survey estimates carry margins of error (shown on town pages) and lag the market. "$2M+" means the Census caps the figure at $2,000,000. Fetched through the open {ext('https://censusreporter.org', 'Census Reporter')} API; each town links to the official data.census.gov table.</li>
<li><strong>General tax rate</strong>: the 2025 rate per $100 of <em>assessed</em> value, used to compute actual bills. <strong>Effective rate</strong>: per $100 of market value, for comparing towns. Source: {ext('https://www.nj.gov/treasury/taxation/pdf/lpt/gtr/2025taxrates.pdf', 'NJ Division of Taxation, 2025 General Tax Rates')}.</li>
<li><strong>Equalization ratio</strong>: the average ratio of assessed to true value used for tax year 2025, from the {ext('https://www.nj.gov/treasury/taxation/pdf/lptval/2024/2024TEV.pdf', 'Table of Equalized Valuations certified Oct 1, 2024')}. A low ratio means assessments sit well below market value.</li>
<li><strong>Illustrative tax</strong> = median value × effective rate. A back-of-envelope number, not a quote.</li>
<li><strong>Listings</strong>: we don't copy or republish MLS or portal listings or photos. The links open Realtor.com or Zillow searches for that town.</li>
</ul>
<p>Last checked {fmt_date(REDATA.get('generated', TODAY.isoformat()))}. Not legal, tax or financial advice. Talk to an NJ real-estate attorney and the local tax assessor.</p>
</div>
{sponsor('agent')}
</div>"""
    page("buying/", "Buying a home at the South Jersey shore: town data", "Median home values, 2025 NJ property tax rates, equalization ratios and flood-map links for South Jersey shore towns, plus an NJ buyer checklist.", body, active="buying/")


CHECKLIST = [
    ("Line up an NJ real-estate attorney before you sign",
     "Contracts prepared by real-estate licensees for 1–4 family homes must include a <strong>three-business-day attorney review</strong> period. Either side's attorney can disapprove the contract in that window; after it, the contract is binding. Weekends and legal holidays don't count.",
     [("N.J.A.C. 11:5-6.2 (Real Estate Commission rule)", "https://www.law.cornell.edu/regulations/new-jersey/N-J-A-C-11-5-6-2"),
      ("NJ Supreme Court, Conley v. Guerrero (2017)", "https://www.njcourts.gov/system/files/court-opinions/2017/a_65_15.pdf")]),
    ("Read the seller's flood-risk disclosure",
     "NJ sellers must say on the property condition disclosure statement whether the property is in a FEMA Special or Moderate Flood Hazard Area, and what they actually know about past flooding, <strong>before you're obligated under the contract</strong>.",
     [("P.L.2023, c.93 (flood risk notification law)", "https://pub.njleg.gov/Bills/2022/PL23/93_.HTM"), ("NJ DEP flood-risk lookup tool", "https://flooddisclosure.nj.gov/"),
      ("NJ DEP: Know your flood risk", "https://dep.nj.gov/climatechange/know-your-flood-risk/")]),
    ("Check the flood map yourself and price flood insurance early",
     "Look up the exact address on FEMA's Flood Map Service Center, then get a flood-insurance quote before attorney review ends. Lenders generally require flood insurance for homes in a Special Flood Hazard Area.",
     [("FEMA Flood Map Service Center", "https://msc.fema.gov/portal/home"), ("FloodSmart (National Flood Insurance Program)", "https://www.floodsmart.gov/")]),
    ("Smoke & carbon-monoxide alarm certificate before closing",
     "Before a one- or two-family home changes hands, the owner must get a certificate of smoke and CO alarm compliance from the local fire official (N.J.A.C. 5:70-2.3). Under P.L.2025, c.19 it now covers smoke alarms, CO alarms and secondary-power-source labels; local fire officials note portable extinguishers have not been required since Feb 3, 2025. Many towns also require their own resale certificate of occupancy, so ask the town.",
     [("N.J.A.C. 5:70-2.3", "https://www.law.cornell.edu/regulations/new-jersey/N-J-A-C-5-70-2-3"),
      ("NJ DCA advisory bulletin on P.L.2025, c.19", "https://www.nj.gov/dca/dfs/pdf/ANNOUNCEMENTS/DCA%20Advisory%20Bulletin%20for%20Licensure.pdf"),
      ("Example: Toms River Bureau of Fire Prevention resale requirements", "https://trfireprevention.com/wp-content/uploads/2025/02/Residential-Resale-Requirements-Feb-2025.pdf")]),
    ("Planning to rent it out? Check rental registration",
     "Many shore towns license or register rentals. <strong>Verified example:</strong> Ocean City requires an annual rental registration (mercantile license) for rental units, including seasonal rentals. We haven't verified other towns' rules yet, so call the town clerk before you count on rental income.",
     [("City of Ocean City rental registration 2025–2026 (PDF)", "https://www.ocnj.us/media/KnightBuilding/Mercantile%20Licensing/RENTAL%20REGISTRATION%202025-2026.pdf")]),
    ("Understand the property-tax math",
     "Bill ≈ assessed value × general tax rate ÷ 100. Assessments often sit below market value (see the town's equalization ratio), so compare towns using the effective rate.",
     [("NJ Division of Taxation: tax rates & equalization tables", "https://www.nj.gov/treasury/taxation/lpt/statdata.shtml"), ("Town-by-town table", None)]),
    ("Budget for closing costs",
     "The companion seller guide covers NJ closing-cost information.",
     [("South Jersey seller guide", SELLER_GUIDE)]),
]


def build_checklist():
    def srcs(lst):
        out = []
        for lbl, url in lst:
            out.append(f'<a href="{u("buying/")}">{e(lbl)}</a>' if url is None else ext(url, e(lbl)))
        return " · ".join(out)
    items = "".join(f'<li class="cl-item"><div class="cl-num">{i}</div><div><h2>{e(h)}</h2><p>{txt}</p><p class="src small">Sources: {srcs(s)} · checked {fmt_date(TODAY.isoformat())}</p></div></li>'
                    for i, (h, txt, s) in enumerate(CHECKLIST, 1))
    body = phero("NJ shore buyer checklist", "Seven things to sort out when buying at the Jersey Shore, each with the official rule or source behind it. Not legal advice: hire an NJ real-estate attorney.", "Save this") + \
        f'<div class="wrap sec"><ol class="checklist">{items}</ol>{sponsor("agent")}<p class="small muted">Rules change; check the linked source. General information only, not legal advice.</p></div>'
    page("buying/checklist/", "NJ shore home buyer checklist", "NJ-specific checklist for buying a shore home: attorney review, flood disclosure, flood insurance, smoke/CO certificate, rental registration and property taxes.", body, active="buying/")


def tile_map():
    cols = []
    for c in COUNTIES:
        ts = [t for t in TOWNS if t["county"] == c]

        def tile(t):
            n = len(near(t["geo"]["lat"], t["geo"]["lon"], PITEMS)) + len(near(t["geo"]["lat"], t["geo"]["lon"], EITEMS))
            heat = "h3" if n >= 80 else "h2" if n >= 30 else "h1" if n else "h0"
            return (f'<a class="tile tile-{heat}{" tile-bay" if t["kind"] == "bay" else ""}" href="{u("towns/" + t["slug"] + "/")}" title="{e(t["name"])}: {n} things to do + events within {NEAR_MI} mi">'
                    f'<span class="tile-n">{e(short_town(t["name"]).replace(" Township", " Twp"))}</span><span class="tile-p">{n}</span></a>')
        cols.append(f"""<section class="tcol"><h3>{e(c)} County</h3>
  <p class="tsub">Ocean-beach towns, north → south</p><div class="tiles">{''.join(tile(t) for t in ts if t['kind'] == 'ocean')}</div>
  <p class="tsub">Bay &amp; mainland towns</p><div class="tiles">{''.join(tile(t) for t in ts if t['kind'] == 'bay')}</div></section>""")
    legend = f'<div class="legend"><span><i class="lg h3"></i>80+</span><span><i class="lg h2"></i>30–79</span><span><i class="lg h1"></i>1–29</span><span><i class="lg h0"></i>none yet</span><span>Number = things to do + upcoming events within {NEAR_MI} mi</span></div>'
    return f'<div class="tilemap">{"".join(cols)}</div>{legend}'


def build_map():
    body = phero("County tile map", f"Every town we cover, by county. Each tile counts things to do plus upcoming events within {NEAR_MI} miles. Bigger number, more going on.", "Where's the action?") + f'<div class="wrap sec">{tile_map()}</div>'
    page("map/", "County tile map of South Jersey shore towns", "Tile map of South Jersey shore towns by county, showing how much is going on nearby.", body, active="map/")


def build_about():
    counts = {k: sum(t["status"] == k for t in TOWNS) for k in STATUS_LABEL}
    rows = "".join(f'<li><span class="pill pill-{k}">{v}</span> {counts[k]} towns</li>' for k, v in STATUS_LABEL.items())
    evsrc = "".join(f'<li>{ext(v["url"], e(v["label"]))} <span class="muted">({e(v["tier"])})</span></li>' for v in EVDATA.get("sources", {}).values())
    body = phero("About, methodology &amp; sources", "How this guide is built, what the labels mean and where everything comes from.") + f"""
<div class="wrap sec prose">
<h2>Things to do</h2>
<p>A hand-picked seed list of attractions, boardwalks, piers, lighthouses, parks, water parks, mini golf, wineries and breweries. A place is published only if <strong>OpenStreetMap has it near the stated town</strong>. We look places up with Nominatim at no more than 1 request per second, with an identifying User-Agent, and cache the results. Short descriptions are quoted from the place's Wikipedia summary or its own website; if neither exists, we say so instead of writing one. Restaurants and bars aren't included yet. Map data © OpenStreetMap contributors (ODbL); Wikipedia text CC BY-SA 4.0.</p>
<h2>Events</h2>
<p>Events come only from public calendars that publish machine-readable feeds or plain web pages: town calendars, Ocean County Tourism, the Greater Wildwood Tourism Authority, Visit Somers Point and the Ocean City Regional Chamber. Meetings, closures and trash notices are filtered out, and recurring listings are collapsed. GitHub Actions refreshes the list every Thursday.</p>
<ul class="small">{evsrc}</ul>
<p><strong>Facebook:</strong> Facebook events require a login, and Facebook's terms prohibit automated collection, so we don't scrape them. Where we've verified a town's official Facebook page, the town page links to it as "More on Facebook" (link only). <strong>Not used yet:</strong> casino and arena calendars (Boardwalk Hall, Hard Rock and others) and the Atlantic City and Cape May County tourism calendars load their events through scripts or token-protected APIs, so we skip them. We don't scrape Eventbrite either.</p>
<h2>Distances</h2>
<p>Distances are <strong>approximate straight-line miles</strong> (haversine formula) from the centre of your chosen town (OpenStreetMap / Nominatim) or from your device location. Your location is used only in your browser and never sent anywhere. These are not driving distances or drive times. Events without a venue location are measured from their town centre.</p>
<h2>Live weather background</h2>
<p>The sky behind the homepage (sun, stars, clouds, rain, snow, fog, storms) follows the current conditions near your chosen town. Your browser asks the US {ext("https://www.weather.gov/documentation/services-web-api", "National Weather Service API")} (<code>api.weather.gov</code>) for the latest observation at the nearest NWS station, falling back to the hourly forecast. It's public-domain data, free, with no API key. Only the town's coordinates are sent, never your device location. Results are cached in your browser for 15 minutes. If the request fails, you get the plain night-sky look. Weather is for decoration: check {ext("https://www.weather.gov/phi/", "NWS Mount Holly")} for real forecasts and warnings. Not endorsed by NOAA/NWS.</p>
<h2>Ask Google AI</h2>
<p>The "Ask Google AI" box opens Google's AI Mode (<code>google.com/search?udm=50</code>) in a new tab with your question plus "South Jersey shore". Nothing is embedded, no API keys are used, and we don't check Google's answers.</p>
<h2>Beach rules: what the labels mean</h2>
<ul class="statuslist">{rows}</ul>
<p><strong>Fully verified</strong> means badge rules, free-beach status, lifeguards, dog rules and alcohol rules were all confirmed on an official municipal page, the municipal code (eCode360) or the official tourism authority. <strong>News report</strong> marks facts from news coverage (mainly Patch's 2026 badge guide) not yet confirmed with the town. Everything else says <em>Not yet verified</em>. Prices are for the <strong>{BADGE_YEAR}</strong> season.</p>
<h2>Buying data</h2>
<p>Census ACS 2020–2024 5-year median home values (table B25077), plus the NJ Division of Taxation's 2025 general and effective tax rates and its Table of Equalized Valuations for tax year 2025. FEMA and NJ DEP flood tools are linked, not copied. No MLS or portal listings or photos are reproduced. The "featured local agent" and "featured local business" boxes are placeholders; nobody has paid for placement.</p>
<h2>The town list</h2>
<p>Ocean-beach municipalities come from the Beaches list in {ext(TOWNDATA['list_source']['url'], "Wikipedia's Jersey Shore article")}, and bayfront and mainland towns from each county's municipality list. Official website links come from Wikipedia infoboxes and were loaded to confirm they work.</p>
<h2>Disclaimer</h2>
<p>Independent guide, not an official source. Things change, sometimes mid-season, so confirm with the organizer or town before you go. Swim only at guarded beaches while lifeguards are on duty. Not legal, tax or financial advice.</p>
</div>"""
    page("about/", "About, methodology & sources", "How the South Jersey Shore Town Guide finds events, places, beach rules and buying data, with every source cited.", body, active="about/")


def build_404():
    body = phero("Washed out to sea", f'That page isn\'t here. Try <a href="{u("things-to-do/")}">things to do</a> or the <a href="{u("towns/")}">town list</a>.')
    page("404.html", "Page not found", "Page not found", body)


def copy_assets():
    adir = OUT / "assets"
    adir.mkdir(parents=True, exist_ok=True)
    for p in SRC.iterdir():
        shutil.copy(p, adir / p.name)


def write_sitemap():
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in [p for p in PAGES if p != "404.html"]:
        pri = "1.0" if p == "" else ("0.9" if p in ("things-to-do/", "events/") else "0.7" if p.startswith("towns/") else "0.6")
        xml.append(f"  <url><loc>{e(absu(p))}</loc><lastmod>{TODAY.isoformat()}</lastmod><priority>{pri}</priority></url>")
    xml.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(xml) + "\n")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {absu('sitemap.xml')}\n")
    (OUT / ".nojekyll").write_text("")


def main():
    missing_geo = [t["slug"] for t in TOWNS if not t.get("geo")]
    if missing_geo:
        raise SystemExit(f"towns missing geo (run scripts/geocode_towns.py): {missing_geo}")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    copy_assets()
    build_home()
    build_things()
    build_events()
    build_towns_index()
    for t in TOWNS:
        build_town(t)
    build_beach_tags()
    build_buying()
    build_checklist()
    build_map()
    build_about()
    build_404()
    write_sitemap()
    (OUT / "data").mkdir(exist_ok=True)
    for f in ("towns.json", "events.json", "places.json", "realestate.json"):
        if (DATA / f).exists():
            shutil.copy(DATA / f, OUT / "data" / f)
    print(f"Built {len(PAGES)} pages into {OUT} (BASE_PATH='{BASE}', SITE_URL='{SITE_URL}', FORM {'on' if FORM_ID else 'off'}) "
          f"· {len(PITEMS)} places · {len(EITEMS)} events")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Static site generator for the South Jersey Shore Town Guide.

Reads  data/towns.json, data/events.json, data/site.json
Writes docs/  (GitHub Pages-ready)

Environment:
  BASE_PATH or PATH_PREFIX  URL prefix the site is served under, e.g. "/sj-shore-guide" for
                            https://user.github.io/sj-shore-guide/ . Default "" (root).
  SITE_URL                  Absolute origin for canonical URLs/sitemap, e.g. https://user.github.io
  FORM_ID                   Newsletter form id. When unset the signup form renders disabled.
  BUILD_DATE                Override "today" (YYYY-MM-DD) for the This Weekend section.
"""
import datetime as dt
import html
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SRC = ROOT / "src"
OUT = ROOT / "docs"

SITE = json.loads((DATA / "site.json").read_text())
TOWNDATA = json.loads((DATA / "towns.json").read_text())
TOWNS = TOWNDATA["towns"]
EVDATA = json.loads((DATA / "events.json").read_text()) if (DATA / "events.json").exists() else {"events": []}
EVENTS = EVDATA.get("events", [])
BYSLUG = {t["slug"]: t for t in TOWNS}

BASE = (os.environ.get("BASE_PATH") or os.environ.get("PATH_PREFIX") or "").strip()
BASE = ("/" + BASE.strip("/")) if BASE.strip("/") else ""
SITE_URL = (os.environ.get("SITE_URL") or SITE["default_site_url"]).rstrip("/")
FORM_ID = os.environ.get("FORM_ID", "").strip()
TODAY = dt.date.fromisoformat(os.environ["BUILD_DATE"]) if os.environ.get("BUILD_DATE") else dt.date.today()
BADGE_YEAR = TOWNDATA.get("badge_year", 2026)
COUNTIES = ["Ocean", "Atlantic", "Cape May"]

e = lambda s: html.escape(str(s if s is not None else ""), quote=True)


def u(path=""):
    """Internal URL with base prefix. path like 'towns/brigantine/'."""
    return f"{BASE}/{path.lstrip('/')}"


def absu(path=""):
    return SITE_URL + u(path)


def fmt_date(iso):
    d = dt.date.fromisoformat(iso[:10])
    return d.strftime("%b %-d, %Y")


def money(v):
    if v is None:
        return None
    return "Free" if v == 0 else f"${v:g}"


# ----------------------------------------------------------------- icons (inline SVG)
ICON = {
    "badge": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16v10H4z" fill="none" stroke="currentColor" stroke-width="1.8" rx="2"/><circle cx="9" cy="12" r="2" fill="currentColor"/><path d="M13 10.5h4M13 13.5h3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "free": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8 12.5l2.6 2.6L16 9.6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "guard": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 21V9h10v12M5 9h14l-2-5H7z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M7 14h10" stroke="currentColor" stroke-width="1.8"/></svg>',
    "dog": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 10l-2-4 4 1 2-2h4l2 2 4-1-2 4v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><circle cx="10" cy="12" r="1" fill="currentColor"/><circle cx="14" cy="12" r="1" fill="currentColor"/><path d="M11 15.5h2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>',
    "alcohol": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h10l-1 7a4 4 0 0 1-8 0zM12 14v6M8.5 21h7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 4l16 16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "parking": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="4" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M10 17V7h3a3 3 0 0 1 0 6h-3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "boardwalk": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 14h18M3 18h18M6 14v6M12 14v6M18 14v6M5 14l3-6h8l3 6" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>',
    "link": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "cal": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="5" width="17" height="15" rx="3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3.5 10h17M8 3v4M16 3v4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="10" r="2.2" fill="currentColor"/></svg>',
    "cart": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 4h2l2.2 10.5a2 2 0 0 0 2 1.5h7.6a2 2 0 0 0 2-1.6L20 8H6.2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><circle cx="10" cy="20" r="1.4" fill="currentColor"/><circle cx="17" cy="20" r="1.4" fill="currentColor"/></svg>',
}

LOGO = ('<svg class="logo" viewBox="0 0 48 48" aria-hidden="true"><defs><linearGradient id="lg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#ffd27a"/><stop offset="1" stop-color="#ff8a5b"/></linearGradient></defs>'
        '<circle cx="24" cy="20" r="11" fill="url(#lg)"/><path d="M4 30c5 0 5-4 10-4s5 4 10 4 5-4 10-4 5 4 10 4v14H4z" fill="#0b6e99"/>'
        '<path d="M4 36c5 0 5-4 10-4s5 4 10 4 5-4 10-4 5 4 10 4v8H4z" fill="#0a4f78"/></svg>')

WAVES = ('<svg class="hero-waves" viewBox="0 0 1440 220" preserveAspectRatio="none" aria-hidden="true">'
         '<path d="M0 120 C 180 60 360 180 540 120 S 900 60 1080 120 S 1320 170 1440 110 V220 H0Z" fill="rgba(255,255,255,.18)"/>'
         '<path d="M0 150 C 200 100 380 200 620 150 S 1000 90 1200 150 S 1380 180 1440 160 V220 H0Z" fill="rgba(255,255,255,.28)"/>'
         '<path d="M0 185 C 240 150 420 215 720 182 S 1140 150 1440 190 V220 H0Z" fill="#fbf6ec"/></svg>')

STATUS_LABEL = {"verified": "Fully verified", "partial": "Partly verified", "reported": "News-reported only", "stub": "Not yet verified"}


# ----------------------------------------------------------------- layout
def page(path, title, desc, body, *, active="", jsonld=None, extra_head=""):
    canonical = absu(path)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>' if jsonld else ""
    nav = [("", "Home"), ("towns/", "Towns"), ("compare/", "Compare"), ("events/", "Events"), ("map/", "County map"), ("about/", "About & sources")]
    navhtml = "".join(f'<a href="{u(p)}"{" aria-current=page" if active == p else ""}>{n}</a>' for p, n in nav)
    full_title = title if title.startswith(SITE["site_name"]) else f"{title} · {SITE['site_name']}"
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canonical)}">
<meta name="theme-color" content="#0a4f78">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['site_name'])}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:image" content="{e(absu('assets/og.svg'))}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{u('assets/favicon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{u('assets/style.css')}">
{ld}{extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
  <div class="wrap topbar-in">
    <a class="brand" href="{u()}">{LOGO}<span><strong>{e(SITE['site_name'])}</strong><small>Ocean · Atlantic · Cape May</small></span></a>
    <button class="navtoggle" aria-expanded="false" aria-controls="nav">Menu</button>
    <nav id="nav" class="nav">{navhtml}</nav>
  </div>
</header>
<main id="main">
{body}
</main>
{footer()}
<script src="{u('assets/app.js')}" defer></script>
</body>
</html>"""
    dest = OUT / path / "index.html" if (path.endswith("/") or path == "") else OUT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc)
    PAGES.append(path)


PAGES = []


def footer():
    return f"""<footer class="footer">
  <div class="wrap footer-grid">
    <div>
      <a class="brand brand-foot" href="{u()}">{LOGO}<span><strong>{e(SITE['site_name'])}</strong><small>Ocean · Atlantic · Cape May</small></span></a>
      <p class="muted">An independent, volunteer-built guide. Not affiliated with any municipality, county, tourism authority or the State of New Jersey.</p>
    </div>
    <div>
      <h3>Disclaimer</h3>
      <p class="muted small">Rules, prices and hours change. Every fact links to the source we checked and the date we checked it — always confirm with the town before you go. Where we could not verify something, we say <em>Not yet verified</em> and link to the official town site instead of guessing. Swim only when and where lifeguards are on duty.</p>
    </div>
    <div>
      <h3>Explore</h3>
      <ul class="footlinks">
        <li><a href="{u('towns/')}">All towns</a></li><li><a href="{u('compare/')}">Comparison table</a></li>
        <li><a href="{u('events/')}">Upcoming events</a></li><li><a href="{u('about/')}">Methodology &amp; sources</a></li>
        <li><a href="{u('sitemap.xml')}">Sitemap</a></li>
      </ul>
    </div>
  </div>
  <div class="wrap small muted foot-bottom">Built {TODAY.isoformat()} · Badge prices shown are {BADGE_YEAR} season unless labeled · No ads, no trackers.</div>
</footer>"""


# ----------------------------------------------------------------- helpers
def fact(t, key):
    return t["facts"].get(key)


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


def free_label(v):
    return {True: "Yes", False: "No"}.get(v, "Not yet verified")


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
    tier_html = {"official": '<span class="tier tier-off">Official</span>',
                 "official tourism": '<span class="tier tier-tour">Official tourism</span>',
                 "news": '<span class="tier tier-news">News report</span>'}.get(tier, "")
    return (f'<p class="src">{tier_html} Source: <a href="{e(f["source"])}" rel="noopener" target="_blank">{e(f.get("source_label") or f["source"])}</a>'
            f' · <span class="checked">Last checked {fmt_date(f["checked"])}</span></p>')


def not_verified(t, what):
    off = t.get("official_url")
    link = f' Check the <a href="{e(off)}" rel="noopener" target="_blank">official town website</a>.' if off else ""
    return f'<p class="nv"><span class="nv-tag">Not yet verified</span> We have not verified {e(what)} for {e(t["name"])} yet.{link}</p>'


def town_events(slug):
    return [ev for ev in EVENTS if ev["town"] == slug and dt.date.fromisoformat(ev["start"][:10]) >= TODAY]


def weekend_range(today):
    # Upcoming Fri–Sun window (if today is Sat/Sun use the current weekend)
    wd = today.weekday()  # Mon=0
    if wd >= 5:
        start = today
        end = today + dt.timedelta(days=6 - wd)
    else:
        start = today + dt.timedelta(days=4 - wd)
        end = start + dt.timedelta(days=2)
    return start, end


def event_card(ev, show_town=True):
    t = BYSLUG.get(ev["town"], {"name": ev["town"], "slug": ev["town"], "county": ""})
    d = dt.date.fromisoformat(ev["start"][:10])
    when = d.strftime("%a, %b %-d") + (f" · {e(ev['time'])}" if ev.get("time") else "")
    town = f'<a class="ev-town" href="{u("towns/" + t["slug"] + "/")}">{e(t["name"])}</a>' if show_town else ""
    venue = f'<span class="ev-venue">{ICON["pin"]}{e(ev["venue"])}</span>' if ev.get("venue") else ""
    stale = '<span class="tier tier-news">may be outdated</span>' if ev.get("stale") else ""
    return f"""<article class="ev">
  <div class="ev-date"><span class="ev-m">{d.strftime('%b')}</span><span class="ev-d">{d.day}</span></div>
  <div class="ev-body">
    <h3><a href="{e(ev['url'])}" rel="noopener" target="_blank">{e(ev['title'])}</a></h3>
    <p class="ev-meta">{town}<span>{when}</span>{venue}{stale}</p>
    <p class="src small">Source: <a href="{e(ev['url'])}" rel="noopener" target="_blank">{e(ev.get('source_label', 'official calendar'))}</a> · fetched {fmt_date(ev.get('fetched', TODAY.isoformat()))}</p>
  </div>
</article>"""


def town_card(t):
    price, tier = seasonal_display(t)
    price_html = f'<span class="price">{e(price)}{"<sup title=News report>*</sup>" if tier == "news" else ""}</span><span class="price-l">{BADGE_YEAR} season tag</span>' if price else '<span class="price nvp">—</span><span class="price-l">badge price not yet verified</span>'
    chips = []
    fb = t["compare"].get("free_beach")
    if fb is True:
        chips.append('<span class="chip chip-free">Free beach</span>')
    if dog_friendly(t):
        chips.append('<span class="chip chip-dog">Dogs in summer (limited)</span>')
    elif t["compare"].get("dogs_offseason"):
        chips.append('<span class="chip chip-dogoff">Dogs off-season</span>')
    if t["kind"] == "bay":
        chips.append('<span class="chip chip-bay">Bay / mainland</span>')
    n_ev = len(town_events(t["slug"]))
    if n_ev:
        chips.append(f'<span class="chip chip-ev">{n_ev} upcoming event{"s" if n_ev > 1 else ""}</span>')
    data = (f'data-county="{e(t["county"])}" data-free="{1 if fb else 0}" data-dog="{1 if dog_friendly(t) else 0}" '
            f'data-status="{t["status"]}" data-kind="{t["kind"]}" data-name="{e(t["name"].lower())}"')
    return f"""<a class="card town-card st-{t['status']}" href="{u('towns/' + t['slug'] + '/')}" {data}>
  <div class="card-top"><span class="county">{e(t['county'])} County</span>{status_pill(t)}</div>
  <h3>{e(t['name'])}</h3>
  <div class="card-price">{price_html}</div>
  <div class="chips">{''.join(chips)}</div>
</a>"""


# ----------------------------------------------------------------- sections
def tile_map(compact=False):
    cols = []
    for c in COUNTIES:
        ts = [t for t in TOWNS if t["county"] == c]
        ocean = [t for t in ts if t["kind"] == "ocean"]
        bay = [t for t in ts if t["kind"] == "bay"]

        def tile(t):
            short = t["name"].split(" (")[0].replace(" Township", " Twp").replace(" City", "")
            price, tier = seasonal_display(t)
            sub = e(price) if price else "—"
            return (f'<a class="tile tile-{t["status"]} {"tile-bay" if t["kind"] == "bay" else ""}" href="{u("towns/" + t["slug"] + "/")}" '
                    f'title="{e(t["name"])} – {STATUS_LABEL[t["status"]]}"><span class="tile-n">{e(short)}</span><span class="tile-p">{sub}</span></a>')
        cols.append(f"""<section class="tcol">
  <h3>{e(c)} County</h3>
  <p class="tsub">Ocean-beach towns <span class="muted">north → south</span></p>
  <div class="tiles">{''.join(tile(t) for t in ocean)}</div>
  <p class="tsub">Bay &amp; mainland towns</p>
  <div class="tiles">{''.join(tile(t) for t in bay)}</div>
</section>""")
    legend = ('<div class="legend"><span><i class="lg lg-verified"></i>Fully verified</span><span><i class="lg lg-partial"></i>Partly verified</span>'
              '<span><i class="lg lg-reported"></i>News-reported prices</span><span><i class="lg lg-stub"></i>Not yet verified</span>'
              f'<span class="muted">Tile shows {BADGE_YEAR} seasonal tag price</span></div>')
    return f'<div class="tilemap">{"".join(cols)}</div>{legend}'


def compare_table(rows=None, sortable=True):
    rows = rows or TOWNS
    trs = []
    for t in rows:
        price, tier = seasonal_display(t)
        p = prices(t) or {}
        daily = money(p.get("daily")) if p.get("daily") is not None else None
        pr_cell = (f'{e(price)}{"<sup>*</sup>" if tier == "news" else ""}' if price else '<span class="nvs">Not yet verified</span>')
        sortv = 9999 if not price else (0 if price.startswith("Free") else float(price.strip("$").split()[0]) if price.startswith("$") else 9998)
        fb = t["compare"].get("free_beach")
        fbcell = {True: '<span class="yes">Yes</span>', False: '<span class="no">No</span>'}.get(fb, '<span class="nvs">Not yet verified</span>')
        dl = dogs_label(t)
        dcls = "yes" if dog_friendly(t) else ("nvs" if dl == "Not yet verified" else "meh")
        trs.append(f"""<tr data-county="{e(t['county'])}" data-free="{1 if fb else 0}" data-dog="{1 if dog_friendly(t) else 0}" data-status="{t['status']}" data-kind="{t['kind']}" data-name="{e(t['name'].lower())}">
<td data-v="{e(t['name'])}"><a href="{u('towns/' + t['slug'] + '/')}">{e(t['name'])}</a></td>
<td data-v="{COUNTIES.index(t['county'])}">{e(t['county'])}</td>
<td data-v="{sortv}">{pr_cell}</td>
<td data-v="{p.get('daily') if p.get('daily') is not None else 9999}">{e(daily) if daily else '<span class="nvs">—</span>'}</td>
<td data-v="{ {True: 0, False: 1}.get(fb, 2) }">{fbcell}</td>
<td data-v="{dl}"><span class="{dcls}">{e(dl)}</span></td>
<td data-v="{list(STATUS_LABEL).index(t['status'])}">{status_pill(t)}</td>
</tr>""")
    return f"""<div class="table-wrap"><table class="cmp{' sortable' if sortable else ''}">
<thead><tr><th>Town</th><th>County</th><th>Seasonal tag ({BADGE_YEAR})</th><th>Daily</th><th>Free beach</th><th>Dogs on beach</th><th>Status</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table></div>
<p class="small muted">* = price reported by news media (Patch, April 2026), not yet confirmed with the town. Regular in-season price shown; most towns sold cheaper preseason tags until late spring. "Dogs on beach" refers to the summer season unless noted.</p>"""


def filters_bar(target):
    return f"""<div class="filters" data-target="{target}">
  <label class="search"><span class="sr">Search towns</span><input type="search" placeholder="Search a town…" data-f="q"></label>
  <div class="fgroup" role="group" aria-label="County">
    <button class="fbtn on" data-county="">All counties</button>
    {''.join(f'<button class="fbtn" data-county="{e(c)}">{e(c)}</button>' for c in COUNTIES)}
  </div>
  <div class="fgroup" role="group" aria-label="Filters">
    <button class="fbtn toggle" data-toggle="free" aria-pressed="false">{ICON['free']} Free beach</button>
    <button class="fbtn toggle" data-toggle="dog" aria-pressed="false">{ICON['dog']} Dog friendly</button>
    <button class="fbtn toggle" data-toggle="verified" aria-pressed="false">✓ Verified only</button>
    <button class="fbtn toggle" data-toggle="ocean" aria-pressed="false">Ocean beaches only</button>
  </div>
  <p class="fcount small muted" aria-live="polite"></p>
</div>"""


def signup():
    if FORM_ID:
        action = SITE["form_endpoint_template"].replace("{FORM_ID}", FORM_ID)
        form = f"""<form class="signup-form" action="{e(action)}" method="post">
  <label class="sr" for="em">Email</label><input id="em" type="email" name="email" required placeholder="you@example.com">
  <button class="btn btn-sun" type="submit">Get the weekend list</button></form>
  <p class="small muted">We'll only use your email for the weekly shore-towns note. Unsubscribe anytime.</p>"""
    else:
        form = """<form class="signup-form is-disabled" onsubmit="return false" aria-disabled="true">
  <label class="sr" for="em">Email</label><input id="em" type="email" disabled placeholder="Signup coming soon">
  <button class="btn btn-sun" type="button" disabled>Coming soon</button></form>
  <p class="small muted">Placeholder — the email signup is turned off until a form provider is configured (set <code>FORM_ID</code> at build time).</p>"""
    return f"""<section class="signup"><div class="wrap signup-in">
  <div><h2>The weekend shore list</h2><p>Events from official town calendars, badge-price changes each spring, and nothing else.</p></div>
  <div>{form}</div></div></section>"""


def sponsor():
    if not SITE["sponsor"]["enabled"]:
        return ""
    return f"""<aside class="sponsor" aria-label="Featured local business (placeholder)">
  <div class="sponsor-tag">Featured local business · <strong>PLACEHOLDER</strong></div>
  <div class="sponsor-box">
    <svg viewBox="0 0 64 64" aria-hidden="true"><rect x="6" y="18" width="52" height="38" rx="6" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="6 5"/><path d="M6 26h52M18 10l-6 8M46 10l6 8M18 10h28" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>
    <div><p><strong>Your South Jersey business here.</strong></p><p class="small">{e(SITE['sponsor']['text'])}</p></div>
  </div>
</aside>"""


# ----------------------------------------------------------------- pages
def build_home():
    n = len(TOWNS)
    nv = sum(t["status"] == "verified" for t in TOWNS)
    nfree = sum(t["compare"].get("free_beach") is True for t in TOWNS)
    ws, we = weekend_range(TODAY)
    upcoming = [ev for ev in EVENTS if dt.date.fromisoformat(ev["start"][:10]) >= TODAY]
    weekend = [ev for ev in upcoming if ws <= dt.date.fromisoformat(ev["start"][:10]) <= we]
    soon = [ev for ev in upcoming if ev not in weekend][:6]
    ev_towns = sorted({BYSLUG[ev["town"]]["name"] for ev in upcoming if ev["town"] in BYSLUG})
    if weekend:
        wk = "".join(event_card(ev) for ev in weekend)
    else:
        wk = '<p class="empty">No events on the official calendars we track for this weekend. See what\'s coming up next ↓</p>'
    feat = [BYSLUG[s] for s in ["brigantine", "ocean-city", "ventnor-city", "wildwood", "sea-isle-city", "cape-may", "avalon", "longport"] if s in BYSLUG]
    body = f"""
<section class="hero">
  <div class="hero-sun" aria-hidden="true"></div>
  <div class="wrap hero-in">
    <p class="eyebrow">South Jersey Shore · {e(', '.join(COUNTIES))} counties</p>
    <h1>Every shore town.<br><span>Every rule. Every source.</span></h1>
    <p class="lead">Beach tags, free beaches, dog rules, lifeguard hours, parking and this weekend's events — for {n} shore and bay towns from Point Pleasant Beach to Cape May Point. If we couldn't verify it, we say so.</p>
    <div class="hero-cta"><a class="btn btn-sun" href="{u('towns/')}">Find a town</a><a class="btn btn-ghost" href="{u('compare/')}">Compare badge prices</a></div>
    <ul class="stats">
      <li><strong>{n}</strong><span>towns covered</span></li>
      <li><strong>{nv}</strong><span>fully verified</span></li>
      <li><strong>{nfree}</strong><span>free beaches</span></li>
      <li><strong>{len(upcoming)}</strong><span>upcoming events</span></li>
    </ul>
  </div>
  {WAVES}
</section>

<div class="wrap">
  <div class="season-note" role="note"><strong>Off-season heads-up ({TODAY.strftime('%B %Y')}):</strong> {e(SITE['season_note'])}</div>

  <section class="sec" id="weekend">
    <div class="sec-h"><h2>This weekend <span class="muted">{ws.strftime('%a %b %-d')} – {we.strftime('%a %b %-d')}</span></h2><a href="{u('events/')}">All events →</a></div>
    <div class="evlist">{wk}</div>
    <h3 class="sub">Coming up</h3>
    <div class="evlist">{''.join(event_card(ev) for ev in soon) or '<p class="empty">Nothing else upcoming yet.</p>'}</div>
    <p class="small muted">Only from official town calendars we can fetch ({e(', '.join(ev_towns))}). Other towns: use the events-calendar link on each town page.</p>
  </section>

  <section class="sec" id="towns">
    <div class="sec-h"><h2>Pick your beach</h2><a href="{u('towns/')}">All {n} towns →</a></div>
    {filters_bar('#home-cards')}
    <div class="cards" id="home-cards">{''.join(town_card(t) for t in sorted(TOWNS, key=lambda t: (list(STATUS_LABEL).index(t['status']), COUNTIES.index(t['county']) == 0)))}</div>
    <p class="small muted">Sorted with fully verified towns first. Atlantic and Cape May county towns were verified first; Ocean County pages are stubs for now.</p>
  </section>

  <section class="sec" id="map">
    <div class="sec-h"><h2>County tile map</h2><a href="{u('map/')}">Full map →</a></div>
    {tile_map()}
  </section>

  {sponsor()}

  <section class="sec">
    <div class="sec-h"><h2>Quick compare: popular towns</h2><a href="{u('compare/')}">Full table →</a></div>
    {compare_table(feat, sortable=False)}
  </section>
</div>
{signup()}
"""
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE["site_name"], "url": absu(), "description": SITE["tagline"]}
    page("", f"{SITE['site_name']} — South Jersey shore towns, beach tags & events",
         f"Beach badge prices ({BADGE_YEAR}), free beaches, dog rules, lifeguard hours, parking and official events for {n} South Jersey shore towns in Ocean, Atlantic and Cape May counties.",
         body, active="", jsonld=ld)


def build_towns_index():
    body = f"""<section class="phero"><div class="wrap"><h1>All shore towns</h1>
<p class="lead">{len(TOWNS)} municipalities in Ocean, Atlantic and Cape May counties — ocean-beach towns plus bayfront mainland towns. Filter by free beaches or dog-friendly rules.</p></div>{WAVES}</section>
<div class="wrap sec">{filters_bar('#all-cards')}<div class="cards" id="all-cards">{''.join(town_card(t) for t in TOWNS)}</div></div>"""
    page("towns/", "All South Jersey shore towns", "Directory of South Jersey shore and bay towns with beach tag prices, free-beach status and dog rules.", body, active="towns/")


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
    p = prices(t)
    pr = t["facts"].get("prices_reported")
    if not p and not pr:
        return ""
    if p:
        if p.get("free_note"):
            nx = p.get("next_year")
            nxt = ""
            if nx:
                nxt = (f'<div class="nextyear"><strong>{nx["year"]} prices already announced:</strong> daily {money(nx["daily"])}, weekly {money(nx["weekly"])}, '
                       f'seasonal {money(nx["seasonal"])} (preseason {money(nx["preseason"])}). '
                       f'<a href="{e(nx["source"])}" target="_blank" rel="noopener">Source</a></div>')
            return f'<div class="prices"><div class="pbox pbox-free"><span>{BADGE_YEAR}</span><strong>FREE</strong><em>no tags</em></div></div>{nxt}'
        boxes = []
        for k, lbl in (("daily", "Daily"), ("three_day", "3-day"), ("weekly", "Weekly"), ("seasonal", "Seasonal"), ("preseason", "Preseason")):
            if k in p:
                v = p.get(k)
                boxes.append(f'<div class="pbox"><span>{lbl}</span><strong>{e(money(v)) if v is not None else "—"}</strong><em>{"not published" if v is None else ""}</em></div>')
        notes = " ".join(e(p[k]) for k in ("preseason_note", "weekly_note", "missing_note", "conflict_note") if p.get(k))
        src = f'<p class="src"><span class="tier tier-off">Official</span> Prices: <a href="{e(p["source"])}" target="_blank" rel="noopener">{e(p["source_label"])}</a> · <span class="checked">Last checked {fmt_date(p["checked"])}</span></p>'
        return f'<div class="price-head">{BADGE_YEAR} season prices</div><div class="prices">{"".join(boxes)}</div><p class="small muted">{notes}</p>{src}'
    boxes = "".join(f'<div class="pbox pbox-news"><span>{lbl}</span><strong>{e(money(pr.get(k))) if pr.get(k) else "—"}</strong></div>' for k, lbl in (("daily", "Daily"), ("weekly", "Weekly"), ("seasonal", "Seasonal")))
    return (f'<div class="price-head">{BADGE_YEAR} prices as reported by news media</div><div class="prices">{boxes}</div>'
            f'<p class="src"><span class="tier tier-news">News report</span> <a href="{e(pr["source"])}" target="_blank" rel="noopener">{e(pr["source_label"])}</a> · <span class="checked">Last checked {fmt_date(pr["checked"])}</span> — not yet confirmed with the town.</p>')


def build_town(t):
    f = t["facts"]
    cards = []
    for key, label, icon, what in FIELD_ORDER:
        inner = ""
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
            inner += (f'<div class="wtb"><h4>{ICON["cart"]} Where to buy</h4><p>{e(wb["value"])}</p>{source_line(wb)}</div>' if wb
                      else (f'<div class="wtb"><h4>{ICON["cart"]} Where to buy</h4>{not_verified(t, "where to buy tags")}</div>' if t["kind"] == "ocean" else ""))
        else:
            v = f.get(key)
            if v:
                inner = f'<p class="fv">{e(v["value"])}</p>' + (f'<p class="fd">{e(v["detail"])}</p>' if v.get("detail") else "") + source_line(v)
            else:
                inner = not_verified(t, what)
        ok = bool(f.get(key)) or (key == "badge" and f.get("badge_reported"))
        cards.append(f'<section class="fact {"" if ok else "fact-nv"} {"fact-wide" if key == "badge" else ""}"><h2>{ICON[icon]}{label}</h2>{inner}</section>')
    if f.get("beach_access"):
        v = f["beach_access"]
        cards.append(f'<section class="fact"><h2>{ICON["pin"]}Beach access</h2><p class="fv">{e(v["value"])}</p>{source_line(v)}</section>')

    links = []
    if t.get("official_url"):
        links.append(f'<a class="lbtn" href="{e(t["official_url"])}" target="_blank" rel="noopener">{ICON["link"]}Official town website</a>')
    if t.get("tourism_url"):
        links.append(f'<a class="lbtn" href="{e(t["tourism_url"])}" target="_blank" rel="noopener">{ICON["link"]}Official tourism site</a>')
    if t.get("events_calendar_url"):
        links.append(f'<a class="lbtn" href="{e(t["events_calendar_url"])}" target="_blank" rel="noopener">{ICON["cal"]}Official events calendar</a>')
    links.append(f'<a class="lbtn lbtn-soft" href="{e(t["wikipedia"])}" target="_blank" rel="noopener">{ICON["link"]}Wikipedia</a>')
    missing_links = []
    if not t.get("tourism_url"):
        missing_links.append("official tourism site")
    if not t.get("events_calendar_url"):
        missing_links.append("official events calendar")
    ml = (f'<p class="small muted">Not yet verified: {e(", ".join(missing_links))}.' +
          (f' Start from the <a href="{e(t["official_url"])}" target="_blank" rel="noopener">official town website</a>.' if t.get("official_url") else "") + "</p>") if missing_links else ""

    evs = town_events(t["slug"])
    if evs:
        evhtml = "".join(event_card(ev, show_town=False) for ev in evs)
    elif t.get("events_calendar_url"):
        evhtml = f'<p class="empty">No upcoming community events pulled from this town\'s official calendar yet. <a href="{e(t["events_calendar_url"])}" target="_blank" rel="noopener">Check the official calendar →</a></p>'
    else:
        evhtml = '<p class="empty">We don\'t have an official events feed for this town yet.</p>'

    notes = "".join(f"<li>{e(n)}</li>" for n in t.get("notes", []))
    notes_html = f'<section class="notes"><h2>Notes</h2><ul>{notes}</ul></section>' if notes else ""
    same = [x for x in TOWNS if x["county"] == t["county"] and x["slug"] != t["slug"]]
    nearby = "".join(f'<a class="mini mini-{x["status"]}" href="{u("towns/" + x["slug"] + "/")}">{e(x["name"])}</a>' for x in same)

    price, tier = seasonal_display(t)
    quick = [
        (ICON["badge"], "Seasonal tag", (price + ("*" if tier == "news" else "")) if price else "Not yet verified"),
        (ICON["free"], "Free beach", free_label(t["compare"].get("free_beach"))),
        (ICON["dog"], "Dogs", dogs_label(t)),
        (ICON["cal"], "Upcoming events", str(len(evs)) if evs else "—"),
    ]
    qhtml = "".join(f'<div class="q">{i}<span>{l}</span><strong>{e(v)}</strong></div>' for i, l, v in quick)
    kind = "Ocean-beach town" if t["kind"] == "ocean" else "Bayfront / mainland town"
    stub_note = ""
    if t["status"] in ("stub", "reported"):
        stub_note = (f'<div class="stubnote"><strong>This page is a stub.</strong> We haven\'t verified this town\'s beach rules with official sources yet, so most facts show '
                     f'<em>Not yet verified</em>. {"Prices below are news-reported only. " if t["status"] == "reported" else ""}'
                     f'{"Use the official town website link for current rules." if t.get("official_url") else ""}</div>')
    desc = f"{t['name']} ({t['county']} County, NJ): beach badge prices ({BADGE_YEAR}), free beach status, dog rules, lifeguard hours, parking and events — with sources."
    ld = {"@context": "https://schema.org", "@type": "TouristDestination", "name": f"{t['name']}, New Jersey",
          "url": absu(f"towns/{t['slug']}/"), "containedInPlace": {"@type": "AdministrativeArea", "name": f"{t['county']} County, New Jersey"}}
    if t.get("official_url"):
        ld["sameAs"] = [t["official_url"], t["wikipedia"]]
    body = f"""
<section class="thero thero-{t['status']}">
  <div class="wrap">
    <nav class="crumbs small"><a href="{u()}">Home</a> / <a href="{u('towns/')}">Towns</a> / <span>{e(t['county'])} County</span></nav>
    <div class="thero-top"><span class="county">{e(t['county'])} County · {kind}</span>{status_pill(t)}</div>
    <h1>{e(t['name'])}</h1>
    <p class="small thero-meta">Facts checked {fmt_date(TOWNDATA['generated'])} · Badge prices are for the <strong>{BADGE_YEAR}</strong> season · Official URL verified {fmt_date(t.get('official_url_checked', TOWNDATA['generated']))}</p>
    <div class="quick">{qhtml}</div>
  </div>
  {WAVES}
</section>
<div class="wrap town-body">
  {stub_note}
  <div class="facts">{''.join(cards)}</div>
  <section class="links-sec"><h2>Official links</h2><div class="lbtns">{''.join(links)}</div>{ml}</section>
  <section class="sec"><div class="sec-h"><h2>Upcoming events</h2><a href="{u('events/')}">All towns →</a></div><div class="evlist">{evhtml}</div></section>
  {notes_html}
  {sponsor()}
  <section class="sec"><h2>Other {e(t['county'])} County towns</h2><div class="minis">{nearby}</div></section>
  <p class="small muted">Town list source: <a href="{e(t['list_source'])}" target="_blank" rel="noopener">{'Wikipedia – Jersey Shore § Beaches' if t['kind'] == 'ocean' else 'Wikipedia – ' + e(t['county']) + ' County municipalities'}</a>. Spotted an error or a change? Rules change every season — always confirm with the town.</p>
</div>"""
    page(f"towns/{t['slug']}/", f"{t['name']} beach guide: tags, dogs, lifeguards ({BADGE_YEAR})", desc, body, active="towns/", jsonld=ld)


def build_compare():
    body = f"""<section class="phero"><div class="wrap"><h1>Compare beach badges</h1>
<p class="lead">{BADGE_YEAR} seasonal tag price, free-beach status and summer dog rules side by side. Click a column to sort.</p></div>{WAVES}</section>
<div class="wrap sec">{filters_bar('#cmp-table tbody')}<div id="cmp-table">{compare_table()}</div></div>"""
    page("compare/", f"Beach badge price comparison ({BADGE_YEAR})", f"Compare {BADGE_YEAR} beach tag prices, free beaches and dog rules across South Jersey shore towns.", body, active="compare/")


def build_events():
    upcoming = [ev for ev in EVENTS if dt.date.fromisoformat(ev["start"][:10]) >= TODAY]
    groups = {}
    for ev in upcoming:
        groups.setdefault(dt.date.fromisoformat(ev["start"][:10]).strftime("%B %Y"), []).append(ev)
    gh = "".join(f'<h2 class="month">{m}</h2><div class="evlist">{"".join(event_card(x) for x in evs)}</div>' for m, evs in groups.items()) or '<p class="empty">No upcoming events right now.</p>'
    srcs = EVDATA.get("sources", {})
    srows = "".join(f'<li><a href="{u("towns/" + s + "/")}">{e(BYSLUG[s]["name"]) if s in BYSLUG else e(s)}</a>: {e(v)}</li>' for s, v in srcs.items())
    body = f"""<section class="phero"><div class="wrap"><h1>Upcoming shore-town events</h1>
<p class="lead">Built only from official town and tourism calendars we can fetch. Government meetings and office closures are filtered out. Events list refreshed {fmt_date(EVDATA.get('generated', TODAY.isoformat()))}.</p></div>{WAVES}</section>
<div class="wrap sec">{gh}
<details class="srcdetails"><summary>Calendar feeds checked on the last refresh</summary><ul class="small">{srows}</ul>
<p class="small muted">Towns without an automated feed: open the "Official events calendar" link on each town page.</p></details></div>"""
    page("events/", "Upcoming events in South Jersey shore towns", "Upcoming community events in South Jersey shore towns from official municipal calendars, with source links.", body, active="events/")


def build_map():
    body = f"""<section class="phero"><div class="wrap"><h1>County tile map</h1>
<p class="lead">Every town we track, grouped by county — ocean-beach towns run north to south; bay and mainland towns below. Colors show how well each town is verified.</p></div>{WAVES}</section>
<div class="wrap sec">{tile_map()}</div>"""
    page("map/", "County tile map of South Jersey shore towns", "Tile map of South Jersey shore towns by county, color-coded by verification status and badge price.", body, active="map/")


def build_about():
    counts = {k: sum(t["status"] == k for t in TOWNS) for k in STATUS_LABEL}
    rows = "".join(f'<li><span class="pill pill-{k}">{v}</span> {counts[k]} towns</li>' for k, v in STATUS_LABEL.items())
    srcset = {}
    for t in TOWNS:
        for k, v in t["facts"].items():
            if isinstance(v, dict) and v.get("source"):
                srcset.setdefault(v["source"], (v.get("source_label") or v["source"], v.get("tier", "official"), v.get("checked")))
    srcs = "".join(f'<li><a href="{e(s)}" target="_blank" rel="noopener">{e(l)}</a> <span class="muted">({e(tr)}, checked {fmt_date(c)})</span></li>' for s, (l, tr, c) in sorted(srcset.items(), key=lambda x: x[1][0]))
    body = f"""<section class="phero"><div class="wrap"><h1>About, methodology &amp; sources</h1>
<p class="lead">How this guide is built, what "verified" means, and where every fact comes from.</p></div>{WAVES}</section>
<div class="wrap sec prose">
<h2>The town list</h2>
<p>Ocean-beach municipalities come from the "Beaches" list in <a href="{e(TOWNDATA['list_source']['url'])}" target="_blank" rel="noopener">Wikipedia's Jersey Shore article</a> (Ocean, Atlantic and Cape May county entries, consolidated to municipalities), plus Cape May Point. Bayfront and mainland towns (for example Linwood, Somers Point and Northfield) are added from each county's municipality list. Official website links come from each municipality's Wikipedia infobox and were then loaded to confirm they work.</p>
<h2>What the labels mean</h2>
<ul class="statuslist">{rows}</ul>
<p><strong>Fully verified</strong> means beach badge rules, free-beach status, lifeguard season/hours, dog rules and alcohol rules were all confirmed on an official municipal page, municipal code (eCode360) or the official tourism authority. Parking and boardwalk details are verified where published. <strong>News report</strong> labels mark facts taken from news coverage (mainly Patch's 2026 badge guide) that we have not yet confirmed with the town. Anything else shows <em>Not yet verified</em> with a link to the official town site — we never guess.</p>
<h2>Badge price year</h2>
<p>All prices are for the <strong>{BADGE_YEAR}</strong> summer season unless a page says otherwise. As of {TODAY.strftime('%B %Y')} most towns have not announced {BADGE_YEAR + 1} prices; Upper Township (Strathmere) has, because it starts charging for the first time in {BADGE_YEAR + 1}.</p>
<h2>Events</h2>
<p>Events come only from official municipal calendars we can fetch automatically (WordPress "The Events Calendar" feeds, EvoGov and CivicPlus calendars) plus a small hand-checked list. Meetings, office closures and trash schedules are filtered out.</p>
<h2>Disclaimer</h2>
<p>This is an independent guide, not an official source. Rules, prices, hours and events change — sometimes mid-season. Always check with the municipality before you go. Swim only at guarded beaches while lifeguards are on duty. The "featured local business" box is a placeholder; no business is featured or endorsed, and no business has paid for placement.</p>
<h2>All sources cited ({len(srcset)})</h2>
<ul class="srclist small">{srcs}</ul>
</div>"""
    page("about/", "About, methodology & sources", "How the South Jersey Shore Town Guide is researched and verified, with every source cited.", body, active="about/")


def build_404():
    body = f"""<section class="phero"><div class="wrap"><h1>Washed out to sea</h1><p class="lead">That page isn't here. Try the <a href="{u('towns/')}">town list</a>.</p></div>{WAVES}</section>"""
    page("404.html", "Page not found", "Page not found", body)


def copy_assets():
    adir = OUT / "assets"
    adir.mkdir(parents=True, exist_ok=True)
    for p in SRC.iterdir():
        shutil.copy(p, adir / p.name)


def write_sitemap():
    urls = [p for p in PAGES if p != "404.html"]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in urls:
        pri = "1.0" if p == "" else ("0.8" if p.startswith("towns/") and p != "towns/" else "0.6")
        xml.append(f"  <url><loc>{e(absu(p))}</loc><lastmod>{TODAY.isoformat()}</lastmod><priority>{pri}</priority></url>")
    xml.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(xml) + "\n")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {absu('sitemap.xml')}\n")
    (OUT / ".nojekyll").write_text("")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    copy_assets()
    build_home()
    build_towns_index()
    for t in TOWNS:
        build_town(t)
    build_compare()
    build_events()
    build_map()
    build_about()
    build_404()
    write_sitemap()
    (OUT / "data").mkdir(exist_ok=True)
    shutil.copy(DATA / "towns.json", OUT / "data" / "towns.json")
    shutil.copy(DATA / "events.json", OUT / "data" / "events.json")
    print(f"Built {len(PAGES)} pages into {OUT} (BASE_PATH='{BASE}', SITE_URL='{SITE_URL}', FORM {'on' if FORM_ID else 'off'})")


if __name__ == "__main__":
    main()

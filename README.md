# South Jersey Shore Town Guide

A static guide to the 55 shore and bay municipalities of Ocean, Atlantic and Cape May counties, NJ:
beach tags and prices, free beaches, lifeguards, dog and alcohol rules, parking, boardwalks,
official links, and upcoming events from official town calendars.

Every fact carries a source link and a last-checked date. Anything we couldn't verify says
**Not yet verified** and links to the town's official site.

```bash
python3 scripts/fetch_events.py   # optional: refresh events
python3 build.py                  # generates docs/
python3 -m http.server 8000 -d docs
```

No dependencies beyond Python 3.9+. No CDNs, trackers or external fonts.
Deployment: `.github/workflows/pages.yml` (GitHub Pages; set `BASE_PATH` and `SITE_URL`).
See `MAINTENANCE.md` for the weekly and yearly update routine.

Town list: Wikipedia "Jersey Shore" § Beaches (ocean towns) plus each county's municipality
list (bay towns). Official URLs from Wikipedia infoboxes, checked by hand.

Not affiliated with any municipality. Rules change. Always check the official town source.

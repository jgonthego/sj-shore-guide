# South Jersey Shore Town Guide

A static "what's going on at the shore" guide to the 55 shore and bay municipalities of Ocean,
Atlantic and Cape May counties, NJ. It covers upcoming events from official town and tourism
calendars and things to do (boardwalks, piers, lighthouses, parks, breweries, wineries…), with a
"how far do you want to drive?" filter (approx. straight-line miles). It also has beach-tag
prices and rules, a public-data "Buying at the Shore" snapshot (Census ACS, NJ tax rates and
ratios, FEMA links) and an NJ buyer checklist.

Every fact carries a source link and a last-checked date. Anything we couldn't verify says
**Not yet verified** and links to the town's official site.

```bash
python3 scripts/fetch_events.py   # optional: refresh events
python3 scripts/enrich_places.py  # optional: rebuild things-to-do from the seed + caches
python3 scripts/realestate_data.py # optional: refresh the real-estate snapshot
python3 build.py                  # generates docs/
python3 -m http.server 8000 -d docs
```

No dependencies beyond Python 3.9+. No CDNs, trackers or external fonts.
Live: https://jgonthego.github.io/sj-shore-guide/ — deployed by `.github/workflows/pages.yml`, which runs `build.py` in CI. `docs/` is build output and is not committed.
See `MAINTENANCE.md` for the weekly and yearly update routine.

Town list: Wikipedia "Jersey Shore" § Beaches (ocean towns) plus each county's municipality
list (bay towns). Official URLs from Wikipedia infoboxes, checked by hand.

Not affiliated with any municipality. Rules change. Always check the official town source.

#!/usr/bin/env python3
"""Build data/realestate.json: per-town public buying snapshot.
 * Median value of owner-occupied homes: U.S. Census Bureau ACS 2020-2024 5-year, table B25077,
   fetched via the Census Reporter API (open, no key) — https://censusreporter.org
 * 2025 general & effective tax rates: NJ Division of Taxation "2025 General Tax Rates" PDF
 * Average assessment ratio used for tax year 2025: NJ Division of Taxation 2024 Table of Equalized
   Valuations (certified Oct 1, 2024 for use in tax year 2025)
Raw PDFs/text are cached in research/ (re-download each spring: see MAINTENANCE.md)."""
import json, re, urllib.request, datetime as dt
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "research"
TAXRATE_URL = "https://www.nj.gov/treasury/taxation/pdf/lpt/gtr/2025taxrates.pdf"
TEV_URL = "https://www.nj.gov/treasury/taxation/pdf/lptval/2024/2024TEV.pdf"
ACS_API = "https://api.censusreporter.org/1.0/data/show/acs2024_5yr?table_ids=B25077&geo_ids=060|05000US34001,060|05000US34009,060|05000US34029"
COUNTY_FIPS = {"Atlantic": "001", "Cape May": "009", "Ocean": "029"}
CC = {"01": "Atlantic", "05": "Cape May", "15": "Ocean"}
FIX = {"toms-river": "TOMS RIVER TWP", "upper-township-strathmere": "UPPER TWP", "lower-township": "LOWER TWP", "ocean-township": "OCEAN TWP",
       "long-beach-township": "LONG BEACH TWP", "margate-city": "MARGATE CITY CITY", "ventnor-city": "VENTNOR CITY", "sea-isle-city": "SEA ISLE CITY CITY",
       "ocean-city": "OCEAN CITY CITY", "cape-may": "CAPE MAY CITY", "point-pleasant-beach": "PT PLEASANT BEACH BORO", "point-pleasant": "POINT PLEASANT BORO",
       "atlantic-city": "ATLANTIC CITY CITY"}
TEV_ALIAS = {"LAVALLETTE BORO": "LAVALETTE BORO"}
ACS_FIX = {"toms-river": "Toms River township", "upper-township-strathmere": "Upper township", "lower-township": "Lower township",
           "ocean-township": "Ocean township", "long-beach-township": "Long Beach township", "point-pleasant": "Point Pleasant borough"}

def main():
    towns = json.loads((ROOT / "data/towns.json").read_text())["towns"]
    rates, county = {}, None
    for line in (RES / "nj_2025taxrates.txt").read_text().splitlines():
        m = re.match(r"\s*(\w[\w ]*?) County\s*$", line)
        if m: county = m.group(1).strip()
        m = re.match(r"^([A-Z][A-Z .'-]+?)\s{2,}([\d.]+)\s+([\d.]+)\s*$", line)
        if m and county in COUNTY_FIPS: rates[(county, m.group(1).strip())] = (float(m.group(2)), float(m.group(3)))
    tev = {}
    for line in (RES / "nj_2024TEV.txt").read_text().splitlines():
        m = re.match(r"^\s*(0[15]\d\d|15\d\d)\s+([A-Z][A-Z .'-]+?)\s{2,}[\d,]+\s+([\d.]+)\s", line)
        if m: tev[(CC[m.group(1)[:2]], m.group(2).strip())] = (m.group(1), float(m.group(3)))
    acs = json.loads(urllib.request.urlopen(urllib.request.Request(ACS_API, headers={"User-Agent": "sj-shore-guide/1.0"}), timeout=60).read())
    acs_by_name = {}
    for gid, v in acs["data"].items():
        nm = acs["geography"][gid]["name"]  # "Linwood city, Atlantic County, NJ"
        acs_by_name[nm.lower()] = (gid, v["B25077"]["estimate"]["B25077001"], v["B25077"]["error"]["B25077001"])
    out, today = {}, dt.date.today().isoformat()
    for t in towns:
        c, slug = t["county"], t["slug"]
        base = t["name"].split(" (")[0]
        cands = [FIX[slug]] if slug in FIX else [x for x in [base.upper(), base.upper().replace("TOWNSHIP", "TWP"), base.upper() + " CITY", base.upper() + " BORO",
                 base.upper().replace(" CITY", "") + " CITY", base.upper() + " TWP", base.upper() + " TOWN", base.upper() + " CITY CITY"]]
        rn = next((x for x in cands if (c, x) in rates), None)
        tn = next((x for x in cands if (c, TEV_ALIAS.get(x, x)) in tev), None)
        # ACS name
        key = None
        if slug in ACS_FIX:
            key = f"{ACS_FIX[slug]}, {c} county, nj".lower()
        else:
            for suf in ("city", "borough", "township", "town", "city city"):
                k = f"{base} {suf}, {c} county, nj".lower()
                if k in acs_by_name: key = k; break
            if not key:
                b2 = base.replace(" City", "").replace(" Township", "")
                for suf in ("city", "borough", "township", "city city"):
                    k = f"{b2} {suf}, {c} county, nj".lower()
                    if k in acs_by_name: key = k; break
        a = acs_by_name.get(key) if key else None
        rec = {"checked": today}
        if a and a[1]:
            gid, est, moe = a
            rec["median_home_value"] = {"value": int(est), "moe": int(moe) if moe else None, "topcoded": est >= 2000001,
                "label": "Median value, owner-occupied homes (ACS 2020–2024 5-year, table B25077)",
                "source": f"https://data.census.gov/table/ACSDT5Y2024.B25077?g=060XX00US{gid[7:]}", "via": f"https://censusreporter.org/data/table/?table=B25077&geo_ids={gid}",
                "source_label": "U.S. Census Bureau, ACS 5-year table B25077", "year": "2020–2024", "geo": acs["geography"][gid]["name"]}
        if rn:
            g, e = rates[(c, rn)]
            rec["tax"] = {"year": 2025, "general_rate": g, "effective_rate": e, "district": rn, "source": TAXRATE_URL,
                          "source_label": "NJ Division of Taxation — 2025 General & Effective Tax Rates"}
        if tn:
            code, ratio = tev[(c, TEV_ALIAS.get(tn, tn))]
            rec["ratio"] = {"tax_year": 2025, "average_ratio": ratio, "district_code": code, "source": TEV_URL,
                            "source_label": "NJ Division of Taxation — Table of Equalized Valuations (certified Oct 1, 2024, for tax year 2025)"}
        rec["flood_map"] = {"url": "https://msc.fema.gov/portal/search?AddressQuery=" + urllib.request.quote(f"{base}, NJ"), "label": "FEMA Flood Map Service Center"}
        rec["nj_flood_risk"] = {"url": "https://njfloodmapper.org/", "label": "NJ Flood Mapper (Rutgers / NJ DEP partners)"}
        q = base.replace(" ", "-")
        rec["search_links"] = {
            "realtor": f"https://www.realtor.com/realestateandhomes-search/{q}_NJ",
            "zillow": f"https://www.zillow.com/{q.lower()}-nj/",
        }
        out[slug] = rec
        if not (a and rn and tn): print("partial:", slug, bool(a), rn, tn, key)
    (ROOT / "data/realestate.json").write_text(json.dumps({"generated": today, "acs_release": acs["release"], "towns": out}, indent=1, ensure_ascii=False))
    print("towns:", len(out), "with ACS:", sum(1 for v in out.values() if "median_home_value" in v), "with tax:", sum(1 for v in out.values() if "tax" in v), "with ratio:", sum(1 for v in out.values() if "ratio" in v))

if __name__ == "__main__":
    main()

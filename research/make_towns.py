# One-time seed that produced data/towns.json (2026-10-17). After this, edit data/towns.json directly.
import json, re, sys
sys.path.insert(0, '.')
from towns_seed import T
W = json.load(open('wiki_websites.json'))
C = "2026-10-17"
PATCH = "https://patch.com/new-jersey/across-nj/2026-jersey-shore-beach-badge-guide-see-season-passes-price-changes"
WIKI_LIST = "https://en.wikipedia.org/wiki/Jersey_Shore#Beaches"

def F(value, source, label, tier="official", detail=None):
    d = {"value": value, "source": source, "source_label": label, "tier": tier, "checked": C}
    if detail: d["detail"] = detail
    return d

def slug(n):
    n = re.sub(r"\(.*?\)", lambda m: m.group(0), n)
    return re.sub(r"[^a-z0-9]+", "-", n.lower().replace("(", "").replace(")", "")).strip("-")

URLFIX = {"Barnegat Light": "https://barnegatlight.org/", "Barnegat Township": "https://www.barnegat.net/",
          "Lacey Township": "https://www.laceytownship.org/", "Little Egg Harbor Township": "https://www.leht.com/",
          "Northfield": "https://www.cityofnorthfield.org/", "Ocean Gate": "https://oceangatenjgov.com/",
          "Pleasantville": "https://www.pleasantville-nj.org/", "Somers Point": "https://www.somerspointgov.org/",
          "Point Pleasant Beach": "https://www.pointpleasantbeach.gov/", "Linwood": "http://www.linwoodcity.org/",
          "Ocean City": "https://www.ocnj.us/"}

towns = {}
for county, name, wt, kind in T:
    s = {"Toms River (Ortley Beach / North Beaches)": "toms-river", "Berkeley Township (Island Beach)": "berkeley-township",
         "Ocean Township (Waretown)": "ocean-township", "Lower Township (Diamond Beach)": "lower-township",
         "Upper Township (Strathmere)": "upper-township-strathmere"}.get(name, slug(name))
    towns[s] = {"slug": s, "name": name, "county": county, "kind": kind,
                "wikipedia": "https://en.wikipedia.org/wiki/" + wt.replace(" ", "_"),
                "list_source": WIKI_LIST if kind == "ocean" else "https://en.wikipedia.org/wiki/" + county.replace(" ", "_") + "_County,_New_Jersey#Municipalities",
                "official_url": URLFIX.get(name, W.get(wt) or None), "official_url_checked": C,
                "tourism_url": None, "events_calendar_url": None,
                "badge_year": 2026, "facts": {}, "compare": {}, "notes": []}

def setf(s, **kw):
    towns[s]["facts"].update(kw)

# ---------------- ATLANTIC COUNTY ----------------
B = "https://brigantinebeach.org/beach-tags/"; BB = "https://brigantinebeach.org/beaches-boating-information/"
setf("brigantine",
  badge=F("Required for ages 12+ (June 20 – Sept. 7, 2026)", B, "City of Brigantine – Beach Tags",
          detail="Seniors 65+ free with ID; active military (4 per family) and veterans free. 60–64 preseason $10."),
  prices={"daily": 10, "weekly": 15, "seasonal": 25, "preseason": 20, "preseason_note": "Seasonal $20 if bought by May 31", "source": B, "source_label": "City of Brigantine – Beach Tags", "checked": C},
  where_to_buy=F("Beach Fee Office, 265 42nd St.; beach inspectors when beach is operating; My Beach Mobile app (digital).", B, "City of Brigantine – Beach Tags"),
  free_beach=F("No – tags required in season", B, "City of Brigantine – Beach Tags"),
  lifeguards=F("Limited guarded beaches from Memorial Day weekend (15th St S, 26th St S, 34th St S weekends); fully staffed third week of June through Labor Day weekend; swimming 10:00 am – 5:30 pm while guards are on duty; limited weekend service in September.", BB, "City of Brigantine – Beaches & Boating"),
  dogs=F("Beach (15th St N to SW tip): no dogs May 15 – Sept 15; leashed Sept 16 – May 14. Cooperative Zone (Sandy Lane–Bramble Dr): no dogs Mar 15 – Sept 15. Promenade (9th–15th St N): no dogs at any time.", BB, "City of Brigantine – Beaches & Boating"),
  alcohol=F("Possessing or consuming alcohol is prohibited on municipal beaches (City Code §105, rules list; see also §91-4).", "https://ecode360.com/7164994", "Brigantine City Code Ch. 105"),
  parking=F("Oceanfront beach lots require a permit May 23 – Sept 7, 2026: $10 daily (ParkMobile zone 88203, valid 8 am–6 pm) or $30 seasonal. Lots: Roosevelt Blvd & Brigantine Ave; 16th, 26th, 34th, 38th St & Ocean Ave.", "https://brigantinebeach.org/parking/", "City of Brigantine – Beach Parking"),
  boardwalk=F("Promenade between 9th St North and 15th St North (no dogs at any time).", BB, "City of Brigantine – Beaches & Boating"))
towns["brigantine"].update(events_calendar_url="https://brigantinebeach.org/events/")
towns["brigantine"]["compare"] = {"free_beach": False, "dogs_summer": "no", "dogs_offseason": True}

AC1 = "https://www.acnj.gov/News/View/2542/2026-atlantic-city-guarded-beaches-start-may-23"; AC2 = "https://www.acnj.gov/News/View/1938/atlantic-city-beach-and-boardwalk-rules-strictly-enforced"
setf("atlantic-city",
  badge=F("No beach tags – beach access is free", PATCH, "Patch 2026 Jersey Shore beach badge guide (news)", tier="news"),
  free_beach=F("Yes – free beach access", PATCH, "Patch 2026 Jersey Shore beach badge guide (news)", tier="news"),
  lifeguards=F("2026 guarded beaches started Sat. May 23; guarded 10 am – 6 pm at listed beaches, with more beaches added each weekend toward July.", AC1, "City of Atlantic City news, May 19, 2026"),
  alcohol=F("No outside alcohol in the open container zone; adults 21+ may drink beverages bought from a licensed establishment in/adjacent to the zone in an open plastic cup bearing the seller's name/logo.", AC2, "City of Atlantic City news (July 3, 2024 – rules reminder)", detail="Beach open 6 am – 10 pm; no smoking/vaping on beach or Boardwalk."),
  boardwalk=F("Yes – the Atlantic City Boardwalk. Summer bike hours 6 am – noon between Albany and Connecticut Aves (through Sept 15); 24-hour riding Connecticut Ave to Gardner's Basin; no e-bikes.", AC2, "City of Atlantic City news (July 3, 2024)"))
towns["atlantic-city"].update(events_calendar_url="https://www.acnj.gov/Calendar")
towns["atlantic-city"]["compare"] = {"free_beach": True, "dogs_summer": None, "dogs_offseason": None}

V = "https://www.ventnorcity.org/beach-information/"; VW = "https://www.ventnorcity.org/welcome-to-ventnor-city"
setf("ventnor-city",
  badge=F("Required for ages 12+, Memorial Day – Labor Day", V, "Ventnor City – Beach Information", detail="Seniors: $3.50 seasonal (preseason). Free veterans tags at City Hall. Ventnor badges are also accepted on Margate beaches (city welcome page)."),
  prices={"daily": None, "weekly": None, "seasonal": 20, "preseason": 10, "preseason_note": "$10 if bought before June 1", "missing_note": "No daily or weekly price is published on the city beach page.", "source": V, "source_label": "Ventnor City – Beach Information", "checked": C},
  where_to_buy=F("Ventnor City Hall, 6201 Atlantic Ave (cash/check/card); online at jerseycapetags.com (mailed); My Beach Mobile app (digital); beach checkers.", V, "Ventnor City – Beach Information"),
  free_beach=F("No – badges required in season", V, "Ventnor City – Beach Information"),
  lifeguards=F("Guarded beaches between Memorial Day and Labor Day, 10:00 am – 6:00 pm daily (which beaches varies early/late season – call 609-823-7948).", V, "Ventnor City – Beach Information"),
  dogs=F("Beach: May 15 – Sept 30 leashed dogs only 7–9 pm on the high-tide-washed area; Oct 1 – May 15 leashed on the high-tide-washed area. Boardwalk: no dogs at any time.", V, "Ventnor City – Beach Information", detail="Note: the codified ordinance text (Ch. 'Keeping of Animals') only lists the Oct 1 – May 15 allowance; the city beach page adds the summer 7–9 pm window."),
  alcohol=F("Alcoholic beverages are not permitted on the beach or Ventnor boardwalk during the summer months.", VW, "Ventnor City – Welcome page"),
  parking=F("Metered/kiosk parking exists near the beach (e.g., Suffolk & Somerset, Newport & New Haven Aves). Rates not published on the beach page.", V, "Ventnor City – Beach Information"),
  boardwalk=F("Yes – 1.7-mile residential boardwalk connected to the Atlantic City Boardwalk; summer bike hours (July 1 – Labor Day: weekends 6 am – noon, weekdays daylight); fishing pier at Cambridge Ave.", VW, "Ventnor City – Welcome page"))
towns["ventnor-city"].update(events_calendar_url="https://www.ventnorcity.org/calendar")
towns["ventnor-city"]["compare"] = {"free_beach": False, "dogs_summer": "limited hours", "dogs_offseason": True}

M = "https://margate-nj.com/1199/Beach-Badge-Information"; MI = "https://www.margate-nj.com/DocumentCenter/View/364/2026-Water-and-Sewer-Insert"; MC = "https://ecode360.com/10322881"
setf("margate-city",
  badge=F("Required for ages 12+ during the bathing season", MC, "Margate City Code Ch. 75 (§75-3)", detail="Seniors 65+: $3.50 preseason. Veterans/active military free with ID."),
  prices={"daily": None, "weekly": 10, "seasonal": 20, "preseason": 10, "preseason_note": "$10 until May 31 (2026 city insert)", "weekly_note": "Weekly $10 per City Code §75-2E (Fri noon – Fri noon); not listed on the 2026 flyer.", "missing_note": "No daily badge is listed.", "source": MI, "source_label": "Margate 2026 beach tag insert + City Code §75-2", "checked": C},
  where_to_buy=F("In person only at the Martin Bloom Pavilion (Granville & Huntington Aves, behind the library); My Beach Mobile app; online & shipped via Jersey Cape Tags; mail-in reservation for pickup (by May 31).", MI, "Margate 2026 beach tag insert"),
  free_beach=F("No – badges required in season", MC, "Margate City Code Ch. 75"),
  lifeguards=F("Lifeguard-protected Memorial Day through Labor Day; guarded bathing beaches open 10 am – 6 pm; some beaches guarded after Labor Day when weather permits.", "https://www.margate-nj.com/margate-city-beach-patrol", "Margate City Beach Patrol"),
  dogs=F("Leashed dogs allowed 6–8 am from the Friday of Memorial Day weekend through Sept 30; leashed at all times the rest of the year.", MC, "Margate City Code §75-6Q"),
  alcohol=F("No consumption of alcoholic beverages on the public beaches ($100 penalty).", MC, "Margate City Code §75-6F"))
towns["margate-city"].update(events_calendar_url="https://www.margate-nj.com/Calendar.aspx")
towns["margate-city"]["compare"] = {"free_beach": False, "dogs_summer": "limited hours", "dogs_offseason": True}

L = "https://www.longportnj.gov/pages/beach-information"; L2 = "https://www.longportnj.gov/News/View/153/june-update-for-2026-beach-tag-sales"
setf("longport",
  badge=F("Required for ages 12+", L, "Borough of Longport – Beach Information", detail="Seniors 65+: $20 ($15 preseason). Children 11 and under free."),
  prices={"daily": 5, "weekly": 15, "seasonal": 40, "preseason": 25, "preseason_note": "$25 through June 1", "source": L2, "source_label": "Longport – June update for 2026 beach tag sales", "checked": C},
  where_to_buy=F("Borough Hall (preseason); Longport Community Building, 33rd & Atlantic Aves (from June 6, 9 am–5 pm); jerseycapetags.com (mailed); My Beach Mobile app; mail-in form (pickup only).", L2, "Longport – June update for 2026 beach tag sales"),
  free_beach=F("No – tags required in season", L, "Borough of Longport – Beach Information"),
  lifeguards=F("Guarded beaches from Memorial Day weekend; open full time May 30 through Labor Day, 10 am – 6 pm daily.", L, "Borough of Longport – Beach Information"),
  dogs=F("May 1 – Sept 30: leashed dogs allowed 6:30–8:30 am and 7:00–8:30 pm. Oct 1 – Apr 30: leashed dogs allowed.", L, "Borough of Longport – Beach Information"))
towns["longport"].update(events_calendar_url="https://www.longportnj.gov/Calendar")
towns["longport"]["compare"] = {"free_beach": False, "dogs_summer": "limited hours", "dogs_offseason": True}
towns["longport"]["notes"].append("News outlets reported a $20 weekly tag; the borough's own June 5, 2026 notice lists $15 – we show the official figure.")

setf("linwood")
towns["linwood"].update(events_calendar_url="http://www.linwoodcity.org/main/events.asp")
setf("somers-point", beach_access=F("The city lists a municipal bathing beach among its recreation facilities (badge/lifeguard details not yet verified).", "https://www.somerspointgov.org/mainpages/recreation.asp", "City of Somers Point – Recreation"))

# ---------------- CAPE MAY COUNTY ----------------
O = "https://www.ocnj.us/beachtags"; OF = "https://www.ocnj.us/beach-faqs"
setf("ocean-city",
  badge=F("Required for ages 12+ (June 1 – Sept 7, 2026)", O, "City of Ocean City – Beach Tags"),
  prices={"daily": 10, "weekly": 20, "seasonal": 35, "preseason": 30, "preseason_note": "$30 through May 31", "source": O, "source_label": "City of Ocean City – Beach Tags", "checked": C},
  where_to_buy=F("Seasonal online at store.ocnj.us; City Hall (861 Asbury Ave); Rt. 52 Welcome Center; Henry Knight Building; Aquatic & Fitness Center; 46th St Welcome Center; Music Pier (Memorial Day – Labor Day); tag sellers at beach entrances and boardwalk booths.", O, "City of Ocean City – Beach Tags"),
  free_beach=F("No – tags required in season", O, "City of Ocean City – Beach Tags"),
  lifeguards=F("Ocean City Beach Patrol staffs lifeguards from Memorial Day weekend to mid-September; the 2026 guarding season has ended.", OF, "City of Ocean City – Beach FAQs", detail="Guarded-beach list: https://www.ocnj.us/ocbp_guarded_beaches"),
  dogs=F("No dogs on any beach May 1 – Sept 30; leashed dogs allowed Oct 1 – Apr 30. No dogs between the OC–Longport Bridge and the terminal groin (near Seaview Rd) Mar 15 – Sept 30.", OF, "City of Ocean City – Beach FAQs"),
  alcohol=F("Drinking alcohol on the beach or in public is strictly prohibited.", OF, "City of Ocean City – Beach FAQs"),
  parking=F("Meters $0.50/hr (downtown Asbury Ave) to $2/hr (beach & boardwalk zone); ParkMobile accepted at all meters; municipal lots never exceed $25/day; all municipal lots and street parking free Oct 31 – May 1.", "https://www.ocnj.us/parking", "City of Ocean City – Parking"),
  boardwalk=F("Yes – Boardwalk district with municipal lots at 5th, 8th, 9th St & Boardwalk and Moorlyn Terrace.", "https://www.ocnj.us/parking", "City of Ocean City – Parking"))
towns["ocean-city"].update(events_calendar_url="https://www.ocnj.us/calendar")
towns["ocean-city"]["compare"] = {"free_beach": False, "dogs_summer": "no", "dogs_offseason": True}

U = "https://uppertownship.com/public-safety/beach-patrol/beach-information/"; U2 = "https://uppertownship.com/strathmere-beach-tags/"
setf("upper-township-strathmere",
  badge=F("2026: no beach tags – all Upper Township beaches are free. Beach tags START in 2027.", U, "Upper Township – Beach Information",
          detail="2027 program (Strathmere): ages 16+, Friday before Memorial Day – Sept 30, 9 am–5 pm. Daily $10, weekly $20, seasonal $30 preseason (Oct 1 – Monday after Presidents Day) / $45 in-season. Seasonal tags on sale now at the Clerk's Office and via Jersey Cape Tags."),
  prices={"daily": 0, "weekly": 0, "seasonal": 0, "preseason": None, "free_note": "Free in 2026", "next_year": {"year": 2027, "daily": 10, "weekly": 20, "seasonal": 45, "preseason": 30, "source": U2}, "source": U, "source_label": "Upper Township – Beach Information", "checked": C},
  where_to_buy=F("(2027 tags) Upper Township Clerk's Office, 2100 Tuckahoe Rd, Petersburg; online via Jersey Cape Tags; daily/weekly via MyBeachMobile once live.", U2, "Upper Township – Strathmere Beach Tags"),
  free_beach=F("Yes in 2026 (tags begin 2027)", U, "Upper Township – Beach Information"),
  lifeguards=F("Strathmere beaches protected 10 am – 5 pm Mon–Thu and 10 am – 5:30 pm Fri–Sun in season; Beesley's Point 10 am – 5 pm daily. All beaches are unprotected for the rest of 2026.", U, "Upper Township – Beach Information"),
  dogs=F("No dogs on any Upper Township beach Mar 15 – Sept 30.", U, "Upper Township – Beach Information"),
  alcohol=F("Alcoholic beverages are not permitted on Upper Township beaches.", U, "Upper Township – Beach Information"),
  parking=F("Free on-street parking in Strathmere; parking available at Beesley's Point.", U, "Upper Township – Beach Information"))
towns["upper-township-strathmere"].update(events_calendar_url="https://uppertownship.com/events/")
towns["upper-township-strathmere"]["compare"] = {"free_beach": True, "dogs_summer": "no", "dogs_offseason": True}

S = "https://www.seaislecitynj.us/departments/beachtag"; SP = "https://visitsicnj.com/beach-policies"
setf("sea-isle-city",
  badge=F("Required for ages 12+, Memorial Day weekend – Labor Day, 10 am – 5 pm. Wednesdays are FREE beach days (except July 4).", S, "Sea Isle City – Beach Tag office",
          detail="Free weekly tags for active military & family; one free season tag per veteran. City's 2027 schedule keeps the $25 → $30 price step on May 16."),
  prices={"daily": 10, "weekly": 15, "seasonal": 30, "preseason": 25, "preseason_note": "$25 if bought by May 15", "source": S, "source_label": "Sea Isle City – Beach Tag office", "checked": C},
  where_to_buy=F("Welcome Center Beach Tag Office, 300 JFK Blvd (Apr 1 – Labor Day); City Hall Tax Office; 24/7 cash vending machine in City Hall lobby (233 JFK Blvd); jerseycapetags.com; My Beach Mobile app; on the beach.", S, "Sea Isle City – Beach Tag office"),
  free_beach=F("No – but Wednesdays are free beach days", S, "Sea Isle City – Beach Tag office"),
  dogs=F("No dogs on beaches, beach approaches, dune paths, public parks or the Promenade May 15 – Sept 30.", SP, "Sea Isle City Tourism – Policies & Regulations"),
  alcohol=F("Consumption of alcoholic beverages is prohibited in all public areas year-round.", SP, "Sea Isle City Tourism – Policies & Regulations"),
  parking=F("Paid May 15 – Labor Day via ParkMobile only (no meters/cash): $0.25 per 15 min + fees. Mon–Sat 9 am – 11 pm, Sun noon – 11 pm; marina district 6 am – 11 pm. Free lots: 4th–7th St & Landis Ave, 94th St & Landis Ave.", "https://visitsicnj.com/parking-information", "Sea Isle City Tourism – Parking"),
  boardwalk=F("Yes – the Promenade (no dogs May 15 – Sept 30; backpack restrictions 10 pm – 1 am in summer).", SP, "Sea Isle City Tourism – Policies & Regulations"))
towns["sea-isle-city"].update(tourism_url="https://visitsicnj.com/")
towns["sea-isle-city"]["compare"] = {"free_beach": False, "dogs_summer": "no", "dogs_offseason": None}
towns["sea-isle-city"]["notes"].append("The city calendar page (seaislecitynj.us/calendar) returned a server error when checked on 2026-10-17, so no events are listed yet.")

A = "https://avalonrecreation.org/beach-information"
setf("avalon",
  badge=F("Required for ages 12+, May 23 – Sept 7, 2026. Tags are reciprocal with Stone Harbor.", A, "Avalon Dept. of Recreation – Beach Information", detail="Free for veterans and active military + immediate family with ID."),
  prices={"daily": 10, "weekly": 18, "seasonal": 42, "preseason": 37, "preseason_note": "$37 on or before May 31", "source": A, "source_label": "Avalon Dept. of Recreation – Beach Information", "checked": C},
  where_to_buy=F("Beach Tag Booth next to Avalon Community Hall (30th St & the beach / 3001 Avalon Ave); Tax Collector at Borough Hall (3100 Dune Dr); Avalon Chamber of Commerce (2989 Ocean Dr); online via Jersey Cape Tags.", A, "Avalon Dept. of Recreation – Beach Information"),
  free_beach=F("No – tags required in season", A, "Avalon Dept. of Recreation – Beach Information"),
  lifeguards=F("Protected beaches 10 am – 5 pm, June 5 – Aug 23; limited guarded beaches May 22 – June 4 and Aug 24 – Sept 13 (2026). Beaches closed 11 pm – 4 am.", A, "Avalon Dept. of Recreation – Beach Information"),
  dogs=F("No dogs on the beach Mar 1 – Sept 30; never on the dunes; never on the boardwalk.", A, "Avalon Dept. of Recreation – Beach Information"),
  alcohol=F("Alcoholic beverages are prohibited on the beach.", A, "Avalon Dept. of Recreation – Beach Information"),
  boardwalk=F("Yes – half-mile boardwalk; bikes 5–10 am only; no dogs; closed 11 pm – 4 am.", A, "Avalon Dept. of Recreation – Beach Information"))
towns["avalon"].update(events_calendar_url="https://avalonboro.net/events/")
towns["avalon"]["compare"] = {"free_beach": False, "dogs_summer": "no", "dogs_offseason": True}

SH = "https://stoneharbornj.org/2026-beach-tags-sales-schedule-and-pricing/"; SHB = "https://stoneharbornj.org/beaches-new/"
setf("stone-harbor",
  badge=F("Required for ages 12+, Saturday of Memorial Day weekend – Labor Day, 10 am – 5 pm. Reciprocal with Avalon.", SHB, "Borough of Stone Harbor – Beaches & Beach Tags", detail="Free veterans tag (in person, DD-214 etc.); active-duty military & family tags at the Beach Tag Office after Memorial Day weekend."),
  prices={"daily": 10, "weekly": 18, "seasonal": 42, "preseason": 37, "preseason_note": "$37 through May 31", "conflict_note": "The borough's 2026 pricing page lists a $10 daily tag; its Beaches page lists $8. Confirm with the Beach Tag Office.", "source": SH, "source_label": "Stone Harbor – 2026 Beach Tags: Sales Schedule & Pricing", "checked": C},
  where_to_buy=F("Beach Tag Office (95th St & the beach); Borough Hall (9508 Second Ave, weekdays); Jersey Cape Tags (shipped); RecDesk online order for pickup.", SH, "Stone Harbor – 2026 Beach Tags: Sales Schedule & Pricing"),
  free_beach=F("No – tags required in season", SHB, "Borough of Stone Harbor – Beaches & Beach Tags"),
  lifeguards=F("Lifeguards on duty 10 am – 5 pm, Memorial Day to Labor Day, at designated protected beaches (81st–122nd St).", SHB, "Borough of Stone Harbor – Beaches & Beach Tags"),
  alcohol=F("Alcoholic beverages (and picnics, fires, glass) are prohibited on the beach.", SHB, "Borough of Stone Harbor – Beaches & Beach Tags"))
towns["stone-harbor"].update(events_calendar_url="https://stoneharbornj.org/events/")
towns["stone-harbor"]["compare"] = {"free_beach": False, "dogs_summer": None, "dogs_offseason": None}

WT = "https://wildwoodsnj.com/visitor-information/beach-information/"
setf("north-wildwood",
  badge=F("No beach tags", WT, "Greater Wildwoods Tourism – Beach Information", tier="official tourism"),
  free_beach=F("Yes – free beaches", WT, "Greater Wildwoods Tourism – Beach Information", tier="official tourism"),
  lifeguards=F("Guarded Memorial Day – Labor Day, 10 am – 5:30 pm daily. Beach Patrol HQ: 15th Ave & the beach, 609-522-7500.", WT, "Greater Wildwoods Tourism – Beach Information", tier="official tourism"),
  dogs=F("Oceanfront beach from the 2nd Ave jetty south to 26th Ave: leashed (max 8 ft) 6–9 am and 5:30–9 pm. Never on Hereford Inlet Beach (2nd Ave west to New York Ave).", "https://ecode360.com/8050642", "North Wildwood City Code Ch. 138"),
  alcohol=F("No consumption of alcoholic beverages on the beach, Boardwalk or approaches.", "https://ecode360.com/8050642", "North Wildwood City Code Ch. 138"),
  boardwalk=F("Yes – Boardwalk from 26th Ave northeast to 13th Ave (per city code definition).", "https://ecode360.com/8050642", "North Wildwood City Code Ch. 138"))
towns["north-wildwood"].update(tourism_url="https://wildwoodsnj.com/", events_calendar_url="https://wildwoodsnj.com/events-calendar/")
towns["north-wildwood"]["compare"] = {"free_beach": True, "dogs_summer": "limited hours", "dogs_offseason": True}

WC = "https://ecode360.com/40647572"
setf("wildwood",
  badge=F("No beach tags", WT, "Greater Wildwoods Tourism – Beach Information", tier="official tourism"),
  free_beach=F("Yes – free beaches", WT, "Greater Wildwoods Tourism – Beach Information", tier="official tourism"),
  lifeguards=F("Guarded Memorial Day – Labor Day, 10 am – 5:30 pm daily. Lifeguard HQ: Lincoln Ave & the beach, 609-522-8258.", WT, "Greater Wildwoods Tourism – Beach Information", tier="official tourism"),
  dogs=F("May 15 – Oct 2: dogs only in the designated Dog Beach (Poplar Ave bathing area, ~250 ft each way; enter at Poplar Ave), leashed. Never on the Boardwalk (service dogs excepted).", WC, "City of Wildwood Code §4-1.14 (Ord. 1294-24)", detail="The tourism site still describes a dog beach at Glenwood Ave; the current ordinance designates Poplar Ave."),
  alcohol=F("No alcohol on the beach at any time of year (except city-permitted special events); none on the Boardwalk except designated restaurant/bar areas.", WC, "City of Wildwood Code Ch. 4"),
  boardwalk=F("Yes – Boardwalk from 26th St to Cresse Ave (per city code definition).", WC, "City of Wildwood Code Ch. 4"))
towns["wildwood"].update(tourism_url="https://wildwoodsnj.com/", events_calendar_url="https://wildwoodnj.gov/events")
towns["wildwood"]["compare"] = {"free_beach": True, "dogs_summer": "dog beach", "dogs_offseason": True}

WCP = "https://wildwoodcrest.org/beachpatrol.php"
setf("wildwood-crest",
  badge=F("No beach tags", WT, "Greater Wildwoods Tourism – Beach Information", tier="official tourism"),
  free_beach=F("Yes – free beaches", WT, "Greater Wildwoods Tourism – Beach Information", tier="official tourism"),
  lifeguards=F("Weekends (and Memorial Day) from the last weekend in May to mid-June, then daily mid-June through Labor Day weekend, 10 am – 5:30 pm on all beaches; some beaches the week after Labor Day; all beaches the following weekend.", WCP, "Borough of Wildwood Crest – Beach Patrol"),
  dogs=F("No animals permitted on the beaches (in season).", WCP, "Borough of Wildwood Crest – Beach Patrol", detail="Greater Wildwoods Tourism says dogs are allowed on Wildwood Crest beaches October – May."),
  alcohol=F("No alcohol on the beach at any time of year.", "https://ecode360.com/36065510", "Wildwood Crest Code Ch. 8"))
towns["wildwood-crest"].update(tourism_url="https://wildwoodsnj.com/", events_calendar_url="https://wildwoodcrest.org/events.php")
towns["wildwood-crest"]["compare"] = {"free_beach": True, "dogs_summer": "no", "dogs_offseason": True}

setf("lower-township",
  alcohol=F("No possessing or consuming alcohol on the beach and approaches.", "https://ecode360.com/11490775", "Township of Lower Code – Beach Regulations"))
towns["lower-township"].update(events_calendar_url="https://www.townshipoflower.org/events")

CM = "https://www.capemaycity.com/departments/beachtag"; CMF = "https://www.capemaycity.com/frequently-asked-questions"; CMC = "https://ecode360.com/6657855"
setf("cape-may",
  badge=F("Required for ages 12+, Sat. May 23 – Labor Day (Sept 7), 10 am – 5 pm", CM, "City of Cape May – Beach Tag", detail="Also a 3-day tag ($20). Free tags for active duty military/family and veterans (in person). Tags required to use ADA beach mats."),
  prices={"daily": 10, "weekly": 25, "seasonal": 40, "preseason": 30, "three_day": 20, "preseason_note": "$30 Dec 31 – Apr 30", "source": CM, "source_label": "City of Cape May – Beach Tag", "checked": C},
  where_to_buy=F("City Hall Tax Office (643 Washington St, weekdays); Beach Tag Office (704 Beach Ave, next to Convention Hall); from May 23 at any beach entrance or the Broadway, Gurney, Howard & Madison booths – cash or personal check only; seasonal online via Jersey Cape Tags.", CM, "City of Cape May – Beach Tag"),
  free_beach=F("No – tags required in season", CM, "City of Cape May – Beach Tag"),
  dogs=F("Dogs allowed on the beach and promenade only Sept 15 – May 15 (leashed, with waste bags).", CMC, "City of Cape May Code Ch. 158"),
  alcohol=F("No consuming alcohol or open containers on beaches, boardwalk, promenade or other public places not licensed for it.", "https://ecode360.com/6657695", "City of Cape May Code §134-8"),
  parking=F("Meters in effect from April 1: Green/Orange zones $2/hr (10 am–6 pm, to Oct 31); Blue $2/hr (10 am–5 pm); Yellow $3/hr (10 am–10 pm, to Dec 31); Red $2/hr. Free at Cape May Elementary (Lafayette & Madison) weekends during school and daily in summer until 11 pm.", "https://www.capemaycity.com/parking-meter-information", "City of Cape May – Parking Meter Information"),
  boardwalk=F("Yes – the Promenade (seasonal bike & dog rules apply).", CMC, "City of Cape May Code Ch. 158"))
towns["cape-may"].update(events_calendar_url="https://www.capemaycity.com/calendar")
towns["cape-may"]["compare"] = {"free_beach": False, "dogs_summer": "no", "dogs_offseason": True}
towns["cape-may"]["notes"].append("The city calendar page returned a server error when checked on 2026-10-17, so no events are listed yet.")

CP = "https://capemaypoint.org/beachtags.php"
setf("cape-may-point",
  badge=F("Required for ages 12+ from the Saturday of Father's Day weekend through Labor Day while lifeguards are on duty (2026 entrance sales began June 20). Cape May Point tags are only valid on Cape May Point beaches.", CP, "Borough of Cape May Point – Beach Tags", detail="Free tags for veterans and active service members & families. Commercial (rental) tag $100."),
  prices={"daily": 10, "weekly": 25, "seasonal": 50, "preseason": 40, "preseason_note": "$40 through May 31", "source": CP, "source_label": "Borough of Cape May Point – Beach Tags", "checked": C},
  where_to_buy=F("Borough Hall, 215 Lighthouse Ave (May preseason, by appointment off-season); beach taggers at each entrance from June 20; online via Jersey Cape Tags. In person: cash or check only.", CP, "Borough of Cape May Point – Beach Tags"),
  free_beach=F("No – tags required in season", CP, "Borough of Cape May Point – Beach Tags"),
  lifeguards=F("Lifeguards on duty from the Saturday of Father's Day weekend through Labor Day (tag season). Hours not listed on the tag page.", CP, "Borough of Cape May Point – Beach Tags"),
  dogs=F("No dogs, cats or other animals (except leashed service animals) on any borough beach April 1 – October 31.", "https://capemaypoint.org/uploaded_files/document/Beach%20Management%20Plan%202024.pdf", "Cape May Point Beach Management Plan (2024)"))
towns["cape-may-point"]["compare"] = {"free_beach": False, "dogs_summer": "no", "dogs_offseason": True}


# --- additions (second pass) ---
SB = "https://www.seaislecitynj.us/departments/BeachPatrol/BeachPatrolFAQs"
setf("sea-isle-city", lifeguards=F("Guards on duty 10:00 am – 5:00 pm Monday–Friday, to 5:30 pm on weekends (in season). Swim only in front of a lifeguard.", SB, "Sea Isle City Beach Patrol FAQs"))
towns["sea-isle-city"]["facts"]["dogs"]["detail"] = "Beach Patrol FAQ: dogs allowed on the beach Oct 1 – May 1 from 20th to 93rd St only, licensed, leashed (max 6 ft), cleaned up after."
towns["sea-isle-city"]["compare"]["dogs_offseason"] = True
setf("cape-may", lifeguards=F("Cape May Beach Patrol hours 10:00 am – 5:00 pm; all designated bathing beaches guarded for the 2026 summer season.", "https://www.capemaycity.com/capemaybeachpatrol", "City of Cape May – Beach Patrol"))
setf("stone-harbor", dogs=F("Leashed dogs on the beach between 80th and 122nd Streets: 7 pm to sunset from the Friday before Memorial Day through Labor Day; any time from the day after Labor Day through the Thursday before Memorial Day. Never south of 127th St (Stone Harbor Point).", "https://ecode360.com/10812363", "Stone Harbor Code – Licensing and Regulation of Dogs"))
towns["stone-harbor"]["compare"].update(dogs_summer="limited hours", dogs_offseason=True)

# ---------------- OCEAN COUNTY: news-reported badge snapshot (Patch, Apr 2026) ----------------
PN = "Patch 2026 Jersey Shore beach badge guide (news, as of Apr 1–10, 2026)"
patch = {
 "point-pleasant-beach": ("Badges at private/borough beaches (Jenkinson's, Maryland Ave, Bradshaw's) – prices vary by beach; some 2026 prices not yet set as of April.", None, None, None),
 "bay-head": ("Beaches run by the Bay Head Improvement Association; 2026 membership info not available as of April.", None, None, None),
 "mantoloking": ("Season $145 ($130 through May 25); daily $15.", 15, None, 145),
 "brick-township": ("Season $45 ($30 until May 15); daily $10; Brick Beach 1, 2, 3.", 10, None, 45),
 "toms-river": ("Season $65 ($50 through Memorial Day), ages 13+; daily price not available as of April.", None, None, 65),
 "lavallette": ("Season $65 ($60 through Apr 30); weekly $40; daily $13.", 13, 40, 65),
 "seaside-heights": ("Season $75; weekly $50; daily $13 (ocean). Bay beach $5 weekends/holidays.", 13, 50, 75),
 "seaside-park": ("Season $70 ($65 through June 14); daily $13.", 13, None, 70),
 "berkeley-township": ("Island Beach State Park (state park, not municipal): entry $6/$12 weekdays, $10/$20 weekends (NJ resident/non-resident).", None, None, None),
 "barnegat-light": ("Season $50 ($40 through June 5); weekly $25; daily $10.", 10, 25, 50),
 "harvey-cedars": ("Season $50 ($40 through June 15); weekly $20; daily $7.", 7, 20, 50),
 "long-beach-township": ("Season $50 ($40 through June 15); weekly $20; daily $10.", 10, 20, 50),
 "surf-city": ("Season $55 ($45 through May 31); weekly $25; daily $11.", 11, 25, 55),
 "ship-bottom": ("2026 prices not listed as of April 1.", None, None, None),
 "beach-haven": ("Season $50 ($40 until May 31); weekly $20; daily $10.", 10, 20, 50),
}
for s, (txt, d, w, se) in patch.items():
    towns[s]["facts"]["badge_reported"] = F(txt, PATCH, PN, tier="news")
    if se:
        towns[s]["facts"]["prices_reported"] = {"daily": d, "weekly": w, "seasonal": se, "source": PATCH, "source_label": PN, "checked": C, "tier": "news"}
    towns[s]["compare"] = {"free_beach": False if se else None, "dogs_summer": None, "dogs_offseason": None}

# ---------------- status ----------------
CORE = ["badge", "free_beach", "lifeguards", "dogs", "alcohol"]
for t in towns.values():
    f = t["facts"]
    have = [k for k in CORE if k in f and f[k].get("tier") in ("official", "official tourism")]
    allf = ["badge", "free_beach", "lifeguards", "dogs", "alcohol", "parking", "boardwalk"]
    t["coverage"] = {"verified_fields": [k for k in allf if k in f], "core_verified": len(have), "core_total": len(CORE)}
    if len(have) == len(CORE):
        t["status"] = "verified"
    elif any(v.get("tier") in ("official", "official tourism") for v in f.values() if isinstance(v, dict) and "tier" in v):
        t["status"] = "partial"
    elif f:
        t["status"] = "reported"
    else:
        t["status"] = "stub"
    for k in ("free_beach", "dogs_summer", "dogs_offseason"):
        t["compare"].setdefault(k, None)
    p = f.get("prices")
    t["compare"]["seasonal"] = p.get("seasonal") if p else None
    t["compare"]["daily"] = p.get("daily") if p else None

order = {"Ocean": 0, "Atlantic": 1, "Cape May": 2}
out = {"generated": C, "badge_year": 2026,
       "list_source": {"label": "Wikipedia – Jersey Shore § Beaches (ocean-beach towns, Ocean/Atlantic/Cape May counties) plus bayfront mainland municipalities from each county's municipality list", "url": WIKI_LIST},
       "towns": sorted(towns.values(), key=lambda t: (order[t["county"]], t["kind"] != "ocean", list(towns).index(t["slug"])))}
json.dump(out, open('../data/towns.json', 'w'), indent=1, ensure_ascii=False)
from collections import Counter
print(Counter(t["status"] for t in out["towns"]), len(out["towns"]))
for t in out["towns"]:
    if t["status"] != "stub": print(t["status"], t["slug"], t["coverage"]["verified_fields"])

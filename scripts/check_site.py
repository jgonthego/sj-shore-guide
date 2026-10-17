#!/usr/bin/env python3
"""Crawl the built site from a local server and report broken internal links/assets.
Usage: python3 scripts/check_site.py http://127.0.0.1:8000 [BASE_PATH]"""
import re, sys, urllib.request, urllib.parse
root = sys.argv[1].rstrip('/'); base = (sys.argv[2] if len(sys.argv) > 2 else '').rstrip('/')
seen, bad, queue = set(), [], [base + '/']
while queue:
    p = queue.pop()
    if p in seen: continue
    seen.add(p)
    try:
        r = urllib.request.urlopen(root + p, timeout=10); body = r.read().decode('utf-8', 'replace')
    except Exception as ex:
        bad.append((p, str(ex))); continue
    if not p.endswith('/') and not p.endswith('.html'): continue
    for m in re.findall(r'(?:href|src)="([^"#]+)"', body):
        if m.startswith(('http', 'mailto:', 'tel:')): continue
        q = urllib.parse.urljoin(p, m)
        if q not in seen: queue.append(q)
print(f"checked {len(seen)} internal URLs, {len(bad)} broken")
for b in bad: print("BROKEN", b)
sys.exit(1 if bad else 0)

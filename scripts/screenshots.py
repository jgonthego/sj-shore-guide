#!/usr/bin/env python3
"""Take review screenshots with Playwright + system Chrome.
Usage: /tmp/pwv/bin/python scripts/screenshots.py http://127.0.0.1:8000"""
import sys, asyncio
from playwright.async_api import async_playwright
ROOT = sys.argv[1].rstrip('/')
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True)
        errs = []
        d = await b.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        d.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        d.on('pageerror', lambda ex: errs.append(str(ex)))
        await d.goto(ROOT + '/', wait_until='networkidle'); await d.screenshot(path='/workspace/shore-home.png', full_page=True)
        await d.goto(ROOT + '/towns/brigantine/', wait_until='networkidle'); await d.screenshot(path='/workspace/shore-town.png', full_page=True)
        # filter smoke test
        await d.goto(ROOT + '/towns/', wait_until='networkidle')
        await d.click('[data-toggle=free]'); txt_free = await d.inner_text('.fcount')
        await d.click('[data-toggle=free]'); await d.click('[data-toggle=dog]'); txt_dog = await d.inner_text('.fcount')
        m = await b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        await m.goto(ROOT + '/', wait_until='networkidle'); await m.screenshot(path='/workspace/shore-mobile.png', full_page=False)
        await m.goto(ROOT + '/towns/ocean-city/', wait_until='networkidle'); await m.screenshot(path='/workspace/shore-mobile-town.png', full_page=False)
        print('free filter:', txt_free, '| dog filter:', txt_dog, '| console errors:', errs)
        await b.close()
asyncio.run(main())

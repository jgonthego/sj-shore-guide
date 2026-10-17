#!/usr/bin/env python3
"""Review screenshots + smoke tests with Playwright + system Chrome.
Usage: /tmp/pwv/bin/python scripts/screenshots.py http://127.0.0.1:18437"""
import sys, asyncio
from playwright.async_api import async_playwright
ROOT = sys.argv[1].rstrip('/')

async def counts(pg):
    return await pg.eval_on_selector_all('[data-count]', 'els => els.map(e => e.textContent)')

async def nearest(pg, sec):
    return await pg.eval_on_selector_all(f'[data-sec={sec}] [data-list] > :not([hidden])',
        'els => els.slice(0,3).map(e => (e.querySelector("h3")||e).textContent.trim().slice(0,40) + " [" + (e.querySelector("[data-dist]")||{}).textContent + "]")')

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True)
        errs = []
        def hook(pg):
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
            pg.on('pageerror', lambda ex: errs.append(str(ex)))
        ctx = await b.new_context(viewport={'width': 1440, 'height': 900})
        d = await ctx.new_page(); hook(d)
        await d.goto(ROOT + '/', wait_until='networkidle')
        await d.evaluate('localStorage.clear()'); await d.goto(ROOT + '/', wait_until='networkidle')
        await d.screenshot(path='/workspace/shore2-home.png', full_page=True)
        print('home default:', await counts(d))
        # Linwood 20 mi
        await d.select_option('[data-origin]', 'linwood'); await d.click('.rad[data-r="20"]')
        print('Linwood 20mi:', await counts(d)); print('  nearest places:', await nearest(d, 'place'))
        ex = await d.query_selector('.explorer')
        await d.evaluate('document.querySelector(".explorer").scrollIntoView()')
        await d.screenshot(path='/workspace/shore2-distance.png', full_page=False, clip=None)
        print('URL after:', d.url)
        await d.click('[data-weekend]'); print('Linwood 20mi weekend:', await counts(d)); await d.click('[data-weekend]')
        # Cape May
        await d.select_option('[data-origin]', 'cape-may'); 
        print('Cape May 20mi:', await counts(d)); print('  nearest places:', await nearest(d, 'place'))
        await d.click('.rad[data-r="10"]'); print('Cape May 10mi:', await counts(d))
        await d.click('.rad[data-r="0"]'); print('Cape May any:', await counts(d))
        # deep link
        await d.goto(ROOT + '/things-to-do/?from=cape-may&r=10', wait_until='networkidle'); print('TTD deep link Cape May 10:', await counts(d))
        await d.goto(ROOT + '/events/?from=linwood&r=20', wait_until='networkidle'); print('Events Linwood 20:', await counts(d))
        await d.goto(ROOT + '/towns/linwood/', wait_until='networkidle')
        el = await d.query_selector('#buying'); await el.screenshot(path='/workspace/shore2-realestate.png')
        await d.goto(ROOT + '/buying/', wait_until='networkidle'); await d.screenshot(path='/tmp/shore2-buying.png', full_page=True)
        await d.goto(ROOT + '/towns/', wait_until='networkidle')
        await d.click('[data-toggle=free]'); print('towns free filter:', await d.inner_text('.fcount'))
        for path in ['/beach-tags/', '/buying/checklist/', '/map/', '/towns/linwood/', '/towns/cape-may/', '/about/']:
            r = await d.goto(ROOT + path, wait_until='networkidle'); assert r.status == 200, path
        await d.goto(ROOT + '/towns/linwood/', wait_until='networkidle'); await d.screenshot(path='/tmp/shore2-town.png', full_page=True)
        # Ask AI: capture popup URL
        await d.goto(ROOT + '/', wait_until='networkidle')
        await d.fill('#askai-hero', 'rainy day ideas')
        await d.route('https://www.google.com/**', lambda r: r.fulfill(status=200, body='ok'))
        async with ctx.expect_page() as pi:
            await d.press('#askai-hero', 'Enter')
        pop = await pi.value; print('Ask AI opens:', pop.url); await pop.close()
        m = await b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True); hook(m)
        await m.goto(ROOT + '/', wait_until='networkidle'); await m.screenshot(path='/workspace/shore2-mobile.png', full_page=False)
        await m.screenshot(path='/tmp/shore2-mobile-full.png', full_page=True)
        sw = await m.evaluate('document.documentElement.scrollWidth'); print('mobile scrollWidth:', sw)
        await m.goto(ROOT + '/towns/ocean-city/', wait_until='networkidle'); await m.screenshot(path='/tmp/shore2-mobile-town.png', full_page=False)
        print('mobile town scrollWidth:', await m.evaluate('document.documentElement.scrollWidth'))
        print('console errors:', errs)
        await b.close()
asyncio.run(main())

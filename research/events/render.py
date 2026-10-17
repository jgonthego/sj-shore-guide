import sys, json, asyncio
from playwright.async_api import async_playwright
async def main(url, out):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True)
        pg = await b.new_page()
        caught=[]
        async def onresp(r):
            ct=r.headers.get('content-type','')
            if 'json' in ct or 'calendar' in ct:
                try: caught.append({'url':r.url,'body':(await r.text())[:200000]})
                except: pass
        pg.on('response', onresp)
        await pg.goto(url, wait_until='networkidle', timeout=60000)
        await pg.wait_for_timeout(3000)
        txt = await pg.inner_text('body')
        json.dump({'text':txt,'json':caught}, open(out,'w'))
        print(url, len(txt), [c['url'][:150] for c in caught])
        await b.close()
asyncio.run(main(sys.argv[1], sys.argv[2]))

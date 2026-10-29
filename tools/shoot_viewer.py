"""Headless check of the viewer: serves viewer/ locally, opens a page, reports console errors and saves screenshots.

  python tools/shoot_viewer.py revh                       # full-page screenshot of the Rev H tab
  python tools/shoot_viewer.py revh --views iso,side,front,rear [--no-section] [--explode 0.6]
  python tools/shoot_viewer.py assembly --steps 0,9,17,36,52   # assembly state after each listed step
  python tools/shoot_viewer.py assembly --mid 38               # frame half-way through step 38's animation

Screenshots go to out/shots/. Needs: pip install playwright && python -m playwright install chromium.
three.js loads from cdn.jsdelivr.net (three@0.160.0); --three-dir points at an unpacked npm 'three' package instead,
for machines without internet access
(Google Fonts requests are stubbed in that mode too).
"""
import argparse
import asyncio
import functools
import http.server
import sys
import threading
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "out" / "shots"
GL_ARGS = ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(directory):
    handler = functools.partial(Quiet, directory=str(directory))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


async def set_step(pg, k):
    await pg.evaluate(f"(()=>{{const r=document.getElementById('stepRange'); r.value={k}; r.dispatchEvent(new Event('input'));}})()")


async def main(a):
    SHOTS.mkdir(parents=True, exist_ok=True)
    srv, port = serve(ROOT / "viewer")
    errs = []
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(args=GL_ARGS)
            pg = await b.new_page(viewport={"width": 1300, "height": 950})
            if a.three_dir:
                base = Path(a.three_dir)

                async def route(r):
                    u = r.request.url
                    if "cdn.jsdelivr.net/npm/three@0.160.0/" in u:
                        await r.fulfill(path=str(base / u.split("three@0.160.0/")[1]), content_type="application/javascript")
                    elif "fonts.g" in u:      # no font server offline either
                        await r.fulfill(status=200, body="", content_type="text/css")
                    else:
                        await r.continue_()
                await pg.route("**/*", route)
            pg.on("console", lambda m: errs.append(f"{m.type}: {m.text}") if m.type == "error" else None)
            pg.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
            await pg.goto(f"http://127.0.0.1:{port}/index.html#{a.page}", wait_until="load", timeout=120000)
            await pg.wait_for_timeout(a.wait)
            box = await pg.locator("#c").bounding_box()   # None on the compare and fea pages (no 3D view)
            clip = {k: box[k] for k in ("x", "y", "width", "height")} if box else None
            if a.no_section:
                await pg.click("#secBtn")
            if a.explode is not None:
                await pg.fill("#ex", str(a.explode))
                await pg.dispatch_event("#ex", "input")
            shots = []
            if a.views:
                for v in a.views.split(","):
                    await pg.click(f"[data-view={v}]")
                    await pg.wait_for_timeout(1500)
                    f = SHOTS / f"{a.page}_{v}.png"
                    await pg.screenshot(path=str(f), clip=clip)
                    shots.append(f)
            if a.steps:
                for k in [int(x) for x in a.steps.split(",")]:
                    await set_step(pg, k)
                    await pg.wait_for_timeout(1500)
                    f = SHOTS / f"asm_{k:02d}.png"
                    await pg.screenshot(path=str(f))
                    shots.append(f)
            if a.mid:
                await set_step(pg, a.mid - 1)
                await pg.wait_for_timeout(1200)
                await pg.click("#nextBtn")
                await pg.wait_for_timeout(a.mid_ms)
                f = SHOTS / f"asm_mid_{a.mid:02d}.png"
                await pg.screenshot(path=str(f))
                shots.append(f)
            if not shots:
                f = SHOTS / f"{a.page}_full.png"
                await pg.screenshot(path=str(f), full_page=clip is None)
                shots.append(f)
            await b.close()
    finally:
        srv.shutdown()
    for f in shots:
        print(f)
    print("\n".join(errs[:20]) or "no console errors")
    return 1 if errs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("page", nargs="?", default="revh", help="tab id: revi, assemblyi, fea, revh, assembly, revg, revf, spherical, reve, revd, revc, revb, compare")
    ap.add_argument("--views", help="comma list of iso,side,front,rear")
    ap.add_argument("--no-section", action="store_true")
    ap.add_argument("--explode", type=float)
    ap.add_argument("--steps", help="assembly steps to capture, e.g. 0,9,52")
    ap.add_argument("--mid", type=int, help="assembly step to capture mid-animation")
    ap.add_argument("--mid-ms", type=int, default=900)
    ap.add_argument("--wait", type=int, default=7000, help="ms to wait after load (mesh download + first render)")
    ap.add_argument("--three-dir", help="local unpacked three@0.160.0 package (offline)")
    sys.exit(asyncio.run(main(ap.parse_args())))

#!/usr/bin/env python3
"""
stress_browser.py -- browser-level stress test (headless Chromium via Playwright).

Measures, with a FRESH browser context (cold cache) per trial:
  PLENARY CONFIGS    plenary_static   web_app/ served by a plain static server (the "Plenary alone" baseline)
                     plenary_file     file:// (how a double-clicked copy behaves)
                     plenary_mounted  /plenary/plenary_logos_suite.html straight from the Suite server
                     plenary_iframe   Suite shell -> "Plenary Logos Suite" tab (what James actually uses)
                     For each: navigation->DOMContentLoaded, ->load, transferred MB (CDP, wire bytes),
                     JS heap after settle, DOM node count, total long-task ms (main thread blocked >50 ms),
                     console errors, page errors, failed/4xx/5xx requests.
  SUITE SWEEP        click every top-level tab of the Suite shell for R rounds; per tab: time-to-quiet,
                     new requests, errors; JS heap growth across rounds (leak signal).

Usage:  python tools/stress_browser.py --suite http://127.0.0.1:8821 --static http://127.0.0.1:8831 --out x.json
"""
import argparse, json, os, statistics, sys, time, pathlib
from playwright.sync_api import sync_playwright

LT_INIT = """
window.__lt = 0; window.__ltn = 0;
try { new PerformanceObserver(l => { for (const e of l.getEntries()) { window.__lt += e.duration; window.__ltn++; } }).observe({type:'longtask', buffered:true}); } catch(e) {}
"""


class Probe:
    def __init__(self, ctx, page):
        self.errors, self.pageerrors, self.badresp, self.failed = [], [], [], []
        self.wire = 0
        self.nreq = 0
        page.on("console", lambda m: self.errors.append(m.text[:160]) if m.type == "error" else None)
        page.on("pageerror", lambda e: self.pageerrors.append(str(e)[:160]))
        page.on("requestfailed", lambda r: self.failed.append(r.url[-90:]))
        page.on("response", lambda r: self.badresp.append(f"{r.status} {r.url[-90:]}") if r.status >= 400 else None)
        self.cdp = ctx.new_cdp_session(page)
        self.cdp.send("Network.enable")
        self.cdp.on("Network.loadingFinished", self._fin)
        self.cdp.on("Network.requestWillBeSent", lambda e: setattr(self, "nreq", self.nreq + 1))
        self.cdp.send("Performance.enable")

    def _fin(self, e):
        self.wire += e.get("encodedDataLength", 0)

    def heap_mb(self):
        m = {x["name"]: x["value"] for x in self.cdp.send("Performance.getMetrics")["metrics"]}
        return m.get("JSHeapUsedSize", 0) / 1e6

    def snapshot(self):
        return {"errors": len(self.errors), "pageerrors": len(self.pageerrors), "bad_responses": len(self.badresp),
                "failed_requests": len(self.failed), "sample_errors": (self.errors + self.pageerrors)[:3],
                "sample_bad": self.badresp[:3], "wire_mb": self.wire / 1e6, "requests": self.nreq}


def measure_plenary(browser, url, via_iframe=False, suite_base=None, settle_ms=2500, timeout_ms=240000):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script(LT_INIT)
    page = ctx.new_page()
    pr = Probe(ctx, page)
    t0 = time.perf_counter()
    out = {"url": url}
    try:
        if via_iframe:
            page.goto(suite_base + "/#library/plenary_suite", wait_until="load", timeout=timeout_ms)
            t_shell = time.perf_counter() - t0
            t1 = time.perf_counter()
            page.evaluate("switchTab('plenary_suite')")
            page.wait_for_selector("#plenary-suite-iframe", timeout=30000)
            fr = None
            deadline = time.time() + timeout_ms / 1000
            while time.time() < deadline:
                fr = next((f for f in page.frames if "plenary_logos_suite" in f.url), None)
                if fr:
                    try:
                        if fr.evaluate("document.readyState === 'complete' && document.querySelectorAll('*').length > 100"):
                            break
                    except Exception:
                        pass
                time.sleep(0.1)
            out["shell_dcl_ms"] = t_shell * 1000
            out["tab_to_iframe_complete_ms"] = (time.perf_counter() - t1) * 1000
            out["total_ms"] = (time.perf_counter() - t0) * 1000
            time.sleep(settle_ms / 1000)
            tgt = fr
        else:
            page.goto(url, wait_until="load", timeout=timeout_ms)
            out["total_ms"] = (time.perf_counter() - t0) * 1000
            nav = page.evaluate("(()=>{const n=performance.getEntriesByType('navigation')[0];return {dcl:n.domContentLoadedEventEnd,load:n.loadEventEnd,resp:n.responseEnd,ttfb:n.responseStart}})()")
            out.update({"ttfb_ms": nav["ttfb"], "response_end_ms": nav["resp"], "dcl_ms": nav["dcl"], "load_ms": nav["load"]})
            time.sleep(settle_ms / 1000)
            tgt = page
        out["dom_nodes"] = tgt.evaluate("document.querySelectorAll('*').length")
        out["long_task_ms"] = tgt.evaluate("window.__lt||0") if not via_iframe else None
        out["heap_mb"] = pr.heap_mb()
    except Exception as e:
        out["fatal"] = type(e).__name__ + ": " + str(e)[:200]
    out.update(pr.snapshot())
    ctx.close()
    return out


def suite_sweep(browser, base, rounds=3, quiet_ms=350, cap_ms=9000):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script(LT_INIT)
    page = ctx.new_page()
    pr = Probe(ctx, page)
    t0 = time.perf_counter()
    page.goto(base + "/", wait_until="load", timeout=60000)
    shell_ms = (time.perf_counter() - t0) * 1000
    tabs = page.evaluate("[...document.querySelectorAll('[id^=btn-tab-]')].map(b=>b.id.replace('btn-tab-',''))")
    rows, heaps = [], [pr.heap_mb()]
    for rd in range(rounds):
        for tid in tabs:
            e0, p0, r0, w0 = len(pr.errors), len(pr.pageerrors), pr.nreq, pr.wire
            t1 = time.perf_counter()
            try:
                page.evaluate(f"switchTab('{tid}')")
            except Exception as e:
                rows.append({"round": rd, "tab": tid, "fatal": str(e)[:100]})
                continue
            last_req, quiet_since = pr.nreq, time.perf_counter()
            while (time.perf_counter() - t1) * 1000 < cap_ms:
                time.sleep(0.05)
                if pr.nreq != last_req:
                    last_req, quiet_since = pr.nreq, time.perf_counter()
                elif (time.perf_counter() - quiet_since) * 1000 >= quiet_ms:
                    break
            ms = (time.perf_counter() - t1) * 1000
            visible = page.evaluate(f"(()=>{{const map={{debates:'packs',pope:'packs'}};const t=map['{tid}']||'{tid}';const p=document.getElementById('tab-'+t);return p?p.classList.contains('active'):null}})()")
            rows.append({"round": rd, "tab": tid, "ms_to_quiet": ms, "hit_cap": ms >= cap_ms - 100, "new_requests": pr.nreq - r0,
                         "new_wire_mb": (pr.wire - w0) / 1e6, "new_errors": len(pr.errors) - e0, "new_pageerrors": len(pr.pageerrors) - p0,
                         "pane_active": visible})
        heaps.append(pr.heap_mb())
    snap = pr.snapshot()
    snap["long_task_ms"] = page.evaluate("window.__lt||0")
    ctx.close()
    return {"shell_load_ms": shell_ms, "tabs": tabs, "rows": rows, "heap_mb_by_round": heaps, "totals": snap}


def summarize(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return {"n": len(vals), "min": min(vals), "median": statistics.median(vals), "max": max(vals),
            "mean": statistics.mean(vals), "cv": (statistics.pstdev(vals) / statistics.mean(vals)) if len(vals) > 1 and statistics.mean(vals) else 0}


def _find_chromium_executable():
    import glob
    local = os.environ.get("LOCALAPPDATA", "")
    for pat in (
        os.path.join(local, "ms-playwright", "chromium_headless_shell-*", "chrome-headless-shell-win64", "chrome-headless-shell.exe"),
        os.path.join(local, "ms-playwright", "chromium-*", "chrome-win64", "chrome.exe"),
    ):
        matches = sorted(glob.glob(pat), reverse=True)
        for m in matches:
            if os.path.isfile(m):
                return m
    for sys_path in (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ):
        if os.path.isfile(sys_path):
            return sys_path
    return None


def launch_browser(pw):
    exe = _find_chromium_executable()
    kw = {"headless": True, "args": ["--enable-precise-memory-info"]}
    if exe:
        kw["executable_path"] = exe
    return pw.chromium.launch(**kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="http://127.0.0.1:8821")
    ap.add_argument("--static", default="http://127.0.0.1:8831")
    ap.add_argument("--file", default=r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\web_app\plenary_logos_suite.html")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--out", default="stress_browser.json")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    res = {"when": time.strftime("%Y-%m-%dT%H:%M:%S"), "plenary": {}, "sweep": None}
    with sync_playwright() as pw:
        br = launch_browser(pw)
        cfgs = [
            ("plenary_static", dict(url=a.static + "/plenary_logos_suite.html")),
            ("plenary_file", dict(url=pathlib.Path(a.file).as_uri())),
            ("plenary_mounted", dict(url=a.suite + "/plenary/plenary_logos_suite.html")),
            ("plenary_iframe", dict(url=a.suite + "/#plenary", via_iframe=True, suite_base=a.suite)),
        ]
        if a.only:
            cfgs = [c for c in cfgs if c[0] in a.only.split(",")]
        for name, kw in cfgs:
            trials = []
            for i in range(a.trials):
                t = measure_plenary(br, **kw)
                trials.append(t)
                print(f"[{name} #{i+1}] total={t.get('total_ms',0):8.0f}ms heap={t.get('heap_mb',0):7.1f}MB wire={t.get('wire_mb',0):7.1f}MB err={t.get('errors')}/{t.get('pageerrors')} badresp={t.get('bad_responses')} fatal={t.get('fatal')}", flush=True)
            res["plenary"][name] = {"trials": trials,
                                    "total_ms": summarize([t.get("total_ms") for t in trials]),
                                    "heap_mb": summarize([t.get("heap_mb") for t in trials]),
                                    "wire_mb": summarize([t.get("wire_mb") for t in trials]),
                                    "long_task_ms": summarize([t.get("long_task_ms") for t in trials])}
        if not a.only or "sweep" in a.only:
            res["sweep"] = suite_sweep(br, a.suite, rounds=a.rounds)
            s = res["sweep"]
            slow = sorted([r for r in s["rows"] if "ms_to_quiet" in r], key=lambda r: -r["ms_to_quiet"])[:8]
            print(f"[sweep] shell load {s['shell_load_ms']:.0f}ms tabs={len(s['tabs'])} heap_by_round={[round(h,1) for h in s['heap_mb_by_round']]} totals={s['totals']}")
            for r in slow:
                print(f"   slow tab {r['tab']:<18} round{r['round']} {r['ms_to_quiet']:7.0f}ms req={r['new_requests']} err={r['new_errors']}/{r['new_pageerrors']}")
            bad = [r for r in s["rows"] if r.get("new_errors") or r.get("new_pageerrors") or r.get("fatal") or r.get("pane_active") is False]
            print(f"[sweep] tab-rounds with errors/inactive pane: {len(bad)}")
            for r in bad[:15]:
                print("   ", r)
        br.close()
    json.dump(res, open(a.out, "w", encoding="utf-8"), indent=1, default=str)
    print("wrote", a.out)


if __name__ == "__main__":
    main()

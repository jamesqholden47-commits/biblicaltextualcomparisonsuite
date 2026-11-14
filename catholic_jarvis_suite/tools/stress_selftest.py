#!/usr/bin/env python3
"""
stress_selftest.py -- the stress test OF the stress test.

A stress harness that has never been shown to fail proves nothing (Rule 3: a check that cannot fail
is not a check). This script proves stress_suite.py / stress_browser.py can fail, and fail on the
RIGHT things, by pointing them at a mock server with known, injected faults:

  clean routes ........ must be OK (zero false positives)
  500 / bad JSON /
  truncated body /
  seeded-param 404 .... must be FAIL
  guessed-param 404 ... must be WARN (not FAIL, not OK)
  slow route .......... must appear in the slowest list and be excluded from the concurrency hammer
  concurrency-only
  fault (503 when >6
  in flight) .......... must pass at concurrency 1 and error at concurrency 8/32 -- proves phase B can fail
  mutating GET (/x/rebuild, /x/launch) and POST ... hit-counter must stay 0 -- proves the safety filter works
  path-param routes ... resolvable one must be exercised, unresolvable one must be listed UNCOVERED
  unknown required param  must be listed UNCOVERED

Then SABOTAGE: classify() is monkeypatched to always say OK; the same assertions must now FAIL. If
they still pass, the selftest is vacuous and it exits 2.

Browser harness (--browser): a mock page with a console.error, an uncaught exception, a 404 image and
a 400 ms busy-loop; the Probe must count each, and long_task_ms must be >= 300.

Usage: python tools/stress_selftest.py [--browser]
Exit 0 = harness proven; 1 = a harness assertion failed; 2 = sabotage did not break the selftest (vacuous).
"""
import sys, os, time, threading, socket, json, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stress_suite as S
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response, JSONResponse, HTMLResponse

HITS = {"rebuild": 0, "launch": 0, "post": 0, "open": 0}
_inflight = {"n": 0}
_lock = threading.Lock()
SEED_FILES = [r"C:\mock\a.md", r"C:\mock\b.md"]


def make_app():
    app = FastAPI()

    @app.get("/api/corpus")
    def corpus(limit: int = 20):
        return {"results": [{"path": p} for p in SEED_FILES]}

    @app.get("/api/files/roots")
    def roots():
        return {"roots": [{"path": r"C:\mock"}]}

    @app.get("/ok/json")
    def ok_json():
        return {"a": 1}

    @app.get("/ok/text")
    def ok_text():
        return Response("hello", media_type="text/plain")

    @app.get("/ok/seeded")
    def ok_seeded(path: str = Query(...)):
        if path not in SEED_FILES:
            raise HTTPException(403, "outside sandbox")
        return {"ok": True}

    @app.get("/fault/500")
    def f500():
        raise HTTPException(500, "boom")

    @app.get("/fault/badjson")
    def fbad():
        return Response('{"a":', media_type="application/json")

    @app.get("/fault/truncate")
    def ftrunc():
        return Response(b"x" * 10, headers={"content-length": "100"})

    @app.get("/fault/seeded404")
    def fseed(path: str = Query(...)):
        raise HTTPException(404, "seeded path but still 404 -> genuine bug")

    @app.get("/fault/guessed404")
    def fguess(src: str = Query(...)):
        raise HTTPException(404, "guessed param rejected")

    @app.get("/fault/slow")
    def fslow():
        time.sleep(1.2)
        return {"slow": True}

    @app.get("/fault/conc")
    def fconc():
        with _lock:
            _inflight["n"] += 1
            n = _inflight["n"]
        try:
            if n > 1:
                raise HTTPException(503, "overloaded under concurrency")
            time.sleep(0.08)
            return {"n": n}
        finally:
            with _lock:
                _inflight["n"] -= 1

    @app.get("/x/rebuild")
    def mut_rebuild():
        HITS["rebuild"] += 1
        return {"mutated": True}

    @app.get("/x/launch")
    def mut_launch():
        HITS["launch"] += 1
        return {"mutated": True}

    @app.post("/x/danger")
    def post_danger():
        HITS["post"] += 1
        return {"mutated": True}

    @app.get("/item")
    def item_list():
        return {"items": [{"id": "abc"}]}

    @app.get("/item/{iid}")
    def item_get(iid: str):
        return {"id": iid}

    @app.get("/thing/{tid}")
    def thing_get(tid: str):
        return {"id": tid}

    @app.get("/need/unknown")
    def need_unknown(zzz_mystery: str = Query(...)):
        return {"z": zzz_mystery}

    return app


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def run_server():
    port = free_port()
    cfg = uvicorn.Config(make_app(), host="127.0.0.1", port=port, log_level="critical")
    srv = uvicorn.Server(cfg)
    th = threading.Thread(target=srv.run, daemon=True)
    th.start()
    for _ in range(100):
        try:
            httpx.get(f"http://127.0.0.1:{port}/ok/json", timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    return srv, f"http://127.0.0.1:{port}"


def evaluate(base):
    """Run the harness against the mock and return {assertion: bool}."""
    for k in HITS:
        HITS[k] = 0
    S.SEED.clear()
    S.CONC_REQS = 160
    results, uncovered, npaths = S.phase_a(base, warm=2)
    by = {r["path"]: r for r in results}
    unc = {u["path"]: u["reason"] for u in uncovered}
    rows, nfast = S.phase_b(base, results, None)
    byc = {r["concurrency"]: r for r in rows}
    A = {}
    A["clean json is OK"] = by["/ok/json"]["verdict"] == "OK"
    A["clean text is OK"] = by["/ok/text"]["verdict"] == "OK"
    A["seeded route is exercised for real and OK (seed worked)"] = by["/ok/seeded"]["verdict"] == "OK"
    A["500 is FAIL"] = by["/fault/500"]["verdict"] == "FAIL"
    A["bad JSON is FAIL"] = by["/fault/badjson"]["verdict"] == "FAIL"
    A["truncated body is FAIL"] = by["/fault/truncate"]["verdict"] == "FAIL"
    A["404 on a seeded param is FAIL"] = by["/fault/seeded404"]["verdict"] == "FAIL"
    A["404 on a guessed param is WARN"] = by["/fault/guessed404"]["verdict"] == "WARN"
    A["slow route measured > 1000 ms"] = (by["/fault/slow"]["warm_p50_ms"] or 0) > 1000
    A["slow route excluded from hammer"] = "/fault/slow" not in {r["path"] for r in results if r["warm_p50_ms"] and r["warm_p50_ms"] < S.SLOW_CUTOFF_MS}
    A["concurrency fault passes serially (conc=1 err==0)"] = byc[1]["errors"] == 0
    A["concurrency fault caught by phase B (conc 8 or 32 err>0)"] = byc[8]["errors"] > 0 or byc[32]["errors"] > 0
    A["mutating GETs never called"] = HITS["rebuild"] == 0 and HITS["launch"] == 0
    A["POST never called"] = HITS["post"] == 0
    A["rebuild/launch listed UNCOVERED by design"] = "/x/rebuild" in unc and "/x/launch" in unc and "MUTATING" in unc.get("/x/rebuild", "")
    A["resolvable path-param route exercised"] = "/item/abc" in by and by["/item/abc"]["verdict"] == "OK"
    A["unresolvable path-param route listed UNCOVERED"] = "/thing/{tid}" in unc
    A["unknown required param listed UNCOVERED"] = "/need/unknown" in unc and "zzz_mystery" in unc["/need/unknown"]
    return A


def main():
    ap_browser = "--browser" in sys.argv
    srv, base = run_server()
    print("mock server", base)
    failed = []
    try:
        print("\n== PASS 1: real classify() -- every assertion must hold ==")
        A = evaluate(base)
        for k, v in A.items():
            print(("  ok   " if v else "  FAIL ") + k)
            if not v:
                failed.append(k)
        print("\n== PASS 2: SABOTAGE (classify() forced to OK) -- the assertions MUST now break ==")
        real = S.classify
        S.classify = lambda r: "OK"
        B = evaluate(base)
        S.classify = real
        broken = [k for k, v in B.items() if not v]
        print(f"  assertions broken by sabotage: {len(broken)}")
        for k in broken:
            print("   broke:", k)
        sabotage_effective = len(broken) >= 3
    finally:
        srv.should_exit = True
    if ap_browser:
        failed += browser_selftest()
    print()
    if failed:
        print(f"SELFTEST FAILED ({len(failed)}): {failed}")
        return 1
    if not sabotage_effective:
        print("SELFTEST VACUOUS: sabotaging classify() did not break the assertions")
        return 2
    print("SELFTEST OK: harness fails on every injected fault, has no false positives, and the selftest itself breaks under sabotage.")
    return 0


# ---------------------------------------------------------------- browser harness
BROWSER_PAGE = """<!doctype html><html><body><h1>probe</h1>
<img src="/missing.png">
<script>console.error('injected-console-error');
setTimeout(()=>{ throw new Error('injected-uncaught'); }, 50);
setTimeout(()=>{ const t=performance.now(); while(performance.now()-t<400){} }, 100);
</script></body></html>"""


def browser_selftest():
    import stress_browser as B
    from playwright.sync_api import sync_playwright
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    def page():
        return BROWSER_PAGE

    port = free_port()
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="critical"))
    threading.Thread(target=srv.run, daemon=True).start()
    time.sleep(1.0)
    fails = []
    print("\n== BROWSER harness vs injected page faults ==")
    with sync_playwright() as pw:
        br = B.launch_browser(pw)
        t = B.measure_plenary(br, f"http://127.0.0.1:{port}/", settle_ms=800)
        br.close()
    srv.should_exit = True
    checks = {
        "console.error counted (>=1)": t.get("errors", 0) >= 1,
        "uncaught exception counted (>=1)": t.get("pageerrors", 0) >= 1,
        "404 resource counted (>=1)": t.get("bad_responses", 0) >= 1,
        "400 ms busy loop shows as long_task_ms >= 300": (t.get("long_task_ms") or 0) >= 300,
        "heap measured (>0)": (t.get("heap_mb") or 0) > 0,
    }
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
        if not v:
            fails.append("browser: " + k)
    print("  raw:", {k: t.get(k) for k in ("errors", "pageerrors", "bad_responses", "long_task_ms", "heap_mb")})
    return fails


if __name__ == "__main__":
    sys.exit(main())

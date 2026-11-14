#!/usr/bin/env python3
"""
stress_suite.py -- API-level stress test for the CatholicJarvis Suite (and its mounted /plenary).

WHAT IT DOES (every number it prints is measured, never assumed -- Rule 3/5):
  Phase A  COVERAGE+LATENCY  discover every GET route from /openapi.json, call each one cold + warm,
                             record status / TTFB / total / bytes / JSON-validity. Anything it cannot
                             call safely is listed as UNCOVERED with a reason -- coverage is reported,
                             never implied.
  Phase B  CONCURRENCY       hammer the safe, fast routes at concurrency 1/8/32, record p50/p95/p99,
                             req/s, error rate, and server RSS / CPU delta (psutil).
  Phase C  STATIC            the heavy static assets (plenary_logos_suite.html 74 MB, data json 73 MB):
                             full-download time, throughput, with and without Accept-Encoding: gzip,
                             Range support, ETag/Cache-Control presence.

It NEVER calls a POST/DELETE, nor any GET whose path matches the MUTATING pattern (rebuild/reindex/
launch/open/refresh/clipboard/poll/backup-run) -- those mutate disk or launch processes.

Usage:
  python tools/stress_suite.py --base http://127.0.0.1:8821 --pid <server pid> --out stress_A.json
  python tools/stress_selftest.py                  # the stress-test-of-the-stress-test
"""
import argparse, asyncio, json, re, statistics, sys, time, os
import httpx

MUTATING = re.compile(r"rebuild|reindex|launch|/open|open-external|refresh|clipboard|poll|backup/run|/links/build|/mark|/place|/pin", re.I)
# Safe default values for REQUIRED query params, by name. A route whose required param is not here is UNCOVERED.
DEFAULT_Q = {
    "q": "grace", "query": "grace", "text": "grace", "term": "grace", "search": "grace",
    "ref": "John 1:1", "passage": "John 1:1", "book": "John", "chapter": "1", "verse": "1",
    "limit": "20", "n": "10", "page": "1", "offset": "0", "path": "", "root": "",
    "src": "NET", "title": "x", "html": "x", "license": "", "key": "", "stem": "",
    "preset": "", "ids": "", "a": "", "b": "",
}
SLOW_CUTOFF_MS = 400  # routes slower than this (warm p50) are excluded from the concurrency hammer
CONC_REQS = 160


def pct(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    k = min(len(xs) - 1, max(0, int(round((p / 100.0) * (len(xs) - 1)))))
    return xs[k]


SEED = {}


def seed(client, base):
    """Real, indexed values so path-taking routes are exercised for real instead of rejected as 403/404.
    A route that still 4xx's WITH a real seed is a genuine failure (see classify())."""
    try:
        res = client.get(base + "/api/corpus", params={"limit": 2}, timeout=60).json()["results"]
        SEED["file"], SEED["file2"] = res[0]["path"], res[1]["path"]
        SEED["dir"] = os.path.dirname(res[0]["path"])
        roots = client.get(base + "/api/files/roots", timeout=30).json()["roots"]
        SEED["root"] = roots[0]["path"]
    except Exception as e:
        SEED["error"] = str(e)[:100]


def seeded_value(route_path, name):
    if name in ("a", "b"):
        return SEED.get("file" if name == "a" else "file2")
    if name == "path":
        if re.search(r"/(list|folders)$", route_path):
            return SEED.get("root")
        return SEED.get("file")
    return None


def discover(client, base):
    seed(client, base)
    spec = client.get(base + "/openapi.json", timeout=60).json()
    routes, uncovered = [], []
    for path, ops in spec["paths"].items():
        op = ops.get("get")
        if not op:
            continue
        if MUTATING.search(path):
            uncovered.append({"path": path, "reason": "MUTATING-pattern (not called by design)"})
            continue
        params = op.get("parameters", [])
        if any(p["in"] == "path" for p in params):
            uncovered.append({"path": path, "reason": "path-param (needs resolver)", "_op": True})
            continue
        q, bad = {}, None
        for p in params:
            if p["in"] == "query" and p.get("required"):
                sv = seeded_value(path, p["name"])
                if sv:
                    q[p["name"]] = sv
                elif p["name"] in DEFAULT_Q:
                    q[p["name"]] = DEFAULT_Q[p["name"]]
                else:
                    bad = p["name"]
        if bad:
            uncovered.append({"path": path, "reason": f"required query param '{bad}' has no safe default"})
            continue
        routes.append({"path": path, "query": q})
    return spec, routes, uncovered


def resolve_path_params(client, base, uncovered, routes):
    """Best-effort: resolve {param} routes by sampling a sibling list endpoint. Honest: leftovers stay UNCOVERED."""
    still = []
    for u in uncovered:
        if not u.get("_op"):
            still.append(u)
            continue
        path = u["path"]
        m = re.findall(r"\{(\w+)\}", path)
        resolved = None
        # sibling = path with the trailing /{x} part removed
        sib = re.sub(r"/\{[^/]+\}.*$", "", path)
        try:
            if path == "/plenary/schaff_pdf/{vol}":
                resolved = "/plenary/schaff_pdf/anf01"
            elif path == "/plenary/source_pdf/{key}":
                resolved = "/plenary/source_pdf/nabre"
            elif len(m) == 1 and sib:
                r = client.get(base + sib, timeout=30)
                if r.status_code == 200:
                    j = r.json()
                    items = j if isinstance(j, list) else next((v for v in j.values() if isinstance(v, list)), []) if isinstance(j, dict) else []
                    if items:
                        first = items[0]
                        val = first if isinstance(first, (str, int)) else next((first[k] for k in ("id", "stem", "key", "pid", "ms_id", "ep_id", "name") if isinstance(first, dict) and k in first), None)
                        if val is not None:
                            resolved = path.replace("{" + m[0] + "}", str(val))
        except Exception:
            resolved = None
        if resolved:
            routes.append({"path": resolved, "query": {}, "template": path})
        else:
            u.pop("_op", None)
            still.append(u)
    return still


def call_once(client, base, route):
    url = base + route["path"]
    t0 = time.perf_counter()
    try:
        with client.stream("GET", url, params=route["query"], timeout=60) as r:
            ttfb = (time.perf_counter() - t0) * 1000
            body = b"".join(r.iter_bytes())
            total = (time.perf_counter() - t0) * 1000
            ct = r.headers.get("content-type", "")
            jvalid = None
            if "json" in ct:
                try:
                    json.loads(body)
                    jvalid = True
                except Exception:
                    jvalid = False
            return {"status": r.status_code, "ttfb_ms": ttfb, "total_ms": total, "bytes": len(body), "ct": ct, "json_valid": jvalid}
    except Exception as e:
        return {"status": -1, "error": type(e).__name__ + ": " + str(e)[:120], "ttfb_ms": None, "total_ms": (time.perf_counter() - t0) * 1000, "bytes": 0, "ct": "", "json_valid": None}


def classify(r):
    """FAIL: connection error, 5xx, a JSON content-type with an invalid body, or a 4xx on a route whose
    params are all real seeds / harmless defaults. A 4xx on a route we had to guess params for is WARN."""
    st = set(r["statuses"])
    if -1 in st or any(x >= 500 for x in st):
        return "FAIL"
    if r["json_valid"] is False:
        return "FAIL"
    if any(x >= 400 for x in st):
        return "FAIL" if r.get("seeded_or_plain", True) else "WARN"
    return "OK"


def phase_a(base, warm=4):
    out = []
    with httpx.Client(timeout=60) as c:
        spec, routes, uncovered = discover(c, base)
        uncovered = resolve_path_params(c, base, uncovered, routes)
        for rt in routes:
            cold = call_once(c, base, rt)
            warms = [call_once(c, base, rt) for _ in range(warm)]
            wt = [w["total_ms"] for w in warms if w["status"] == 200]
            out.append({
                "path": rt["path"], "template": rt.get("template"), "query": rt["query"],
                "cold": cold, "warm_p50_ms": statistics.median(wt) if wt else None,
                "warm_max_ms": max(wt) if wt else None,
                "statuses": sorted({w["status"] for w in warms} | {cold["status"]}),
                "bytes": cold["bytes"], "json_valid": cold["json_valid"],
                "seeded_or_plain": all((v in (SEED.get("file"), SEED.get("file2"), SEED.get("root"))) or k in ("limit", "offset", "n", "page", "q", "query")
                                       for k, v in rt["query"].items()),
            })
            out[-1]["verdict"] = classify(out[-1])
    return out, uncovered, len(spec["paths"])


async def _hammer(base, routes, conc, total):
    lat, errs, byroute = [], 0, {}
    sem = asyncio.Semaphore(conc)
    limits = httpx.Limits(max_connections=conc, max_keepalive_connections=conc)
    async with httpx.AsyncClient(timeout=60, limits=limits) as c:
        async def one(i):
            nonlocal errs
            rt = routes[i % len(routes)]
            async with sem:
                t0 = time.perf_counter()
                try:
                    r = await c.get(base + rt["path"], params=rt["query"])
                    ok = r.status_code == 200
                except Exception:
                    ok = False
                ms = (time.perf_counter() - t0) * 1000
                lat.append(ms)
                if not ok:
                    errs += 1
                    byroute[rt["path"]] = byroute.get(rt["path"], 0) + 1
        t0 = time.perf_counter()
        await asyncio.gather(*[one(i) for i in range(total)])
        wall = time.perf_counter() - t0
    return lat, errs, wall, byroute


def phase_b(base, results, pid=None):
    fast = [{"path": r["path"], "query": r["query"]} for r in results
            if r["statuses"] == [200] and r["warm_p50_ms"] is not None and r["warm_p50_ms"] < SLOW_CUTOFF_MS and r["bytes"] < 2_000_000]
    rows = []
    try:
        import psutil
        proc = psutil.Process(pid) if pid else None
    except Exception:
        proc = None
    for conc in (1, 8, 32):
        rss0 = proc.memory_info().rss if proc else None
        if proc:
            proc.cpu_percent(None)
        lat, errs, wall, byroute = asyncio.run(_hammer(base, fast, conc, CONC_REQS))
        cpu = proc.cpu_percent(None) if proc else None
        rss1 = proc.memory_info().rss if proc else None
        rows.append({"concurrency": conc, "requests": CONC_REQS, "routes": len(fast), "errors": errs,
                     "err_by_route": byroute, "rps": CONC_REQS / wall, "p50_ms": pct(lat, 50), "p95_ms": pct(lat, 95),
                     "p99_ms": pct(lat, 99), "max_ms": max(lat), "server_cpu_pct": cpu,
                     "rss_mb_before": rss0 / 1e6 if rss0 else None, "rss_mb_after": rss1 / 1e6 if rss1 else None})
    return rows, len(fast)


def phase_c(base, assets):
    rows = []
    with httpx.Client(timeout=300) as c:
        for a in assets:
            for enc in ("identity", "gzip"):
                t0 = time.perf_counter()
                try:
                    with c.stream("GET", base + a, headers={"Accept-Encoding": enc}) as r:
                        ttfb = (time.perf_counter() - t0) * 1000
                        wire = 0
                        for ch in r.iter_raw():
                            wire += len(ch)
                        total = (time.perf_counter() - t0) * 1000
                        h = r.headers
                        rows.append({"asset": a, "accept_encoding": enc, "status": r.status_code, "ttfb_ms": ttfb, "total_ms": total,
                                     "wire_mb": wire / 1e6, "mb_per_s": (wire / 1e6) / (total / 1000) if total else None,
                                     "content_encoding": h.get("content-encoding"), "etag": h.get("etag"),
                                     "cache_control": h.get("cache-control"), "accept_ranges": h.get("accept-ranges"),
                                     "last_modified": h.get("last-modified")})
                except Exception as e:
                    rows.append({"asset": a, "accept_encoding": enc, "status": -1, "error": str(e)[:120]})
            # Range + conditional probes
            try:
                r = c.get(base + a, headers={"Range": "bytes=0-1023"})
                rows.append({"asset": a, "probe": "range 0-1023", "status": r.status_code, "got": len(r.content)})
                h = c.head(base + a)
                et = h.headers.get("etag")
                if et:
                    r2 = c.get(base + a, headers={"If-None-Match": et})
                    rows.append({"asset": a, "probe": "If-None-Match", "status": r2.status_code, "got": len(r2.content)})
                else:
                    rows.append({"asset": a, "probe": "If-None-Match", "status": None, "note": "no ETag"})
            except Exception as e:
                rows.append({"asset": a, "probe": "range/etag", "status": -1, "error": str(e)[:100]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8821")
    ap.add_argument("--pid", type=int)
    ap.add_argument("--out", default="stress_result.json")
    ap.add_argument("--assets", default="/plenary/plenary_logos_suite.html,/plenary/plenary_logos_data.json")
    ap.add_argument("--skip-static", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    results, uncovered, npaths = phase_a(a.base)
    bad = [r for r in results if r["verdict"] == "FAIL"]
    warn = [r for r in results if r["verdict"] == "WARN"]
    print(f"[A] openapi paths={npaths}  GET called={len(results)}  uncovered={len(uncovered)}  FAIL={len(bad)}  WARN={len(warn)}  seed={ {k: (v[-40:] if isinstance(v, str) else v) for k, v in SEED.items()} }")
    for r in bad:
        print("   FAIL", r["path"], r["statuses"], "json_valid=", r["json_valid"], (r["cold"].get("error") or ""))
    for r in warn:
        print("   WARN", r["path"], r["statuses"])
    for u in uncovered:
        print("   UNCOVERED", u["path"], "--", u["reason"])
    slow = sorted([r for r in results if r["warm_p50_ms"]], key=lambda r: -r["warm_p50_ms"])[:10]
    print("[A] slowest 10 (warm p50 ms, bytes):")
    for r in slow:
        print(f"   {r['warm_p50_ms']:9.1f}  {r['bytes']:>10}  {r['path']}")
    rows, nfast = phase_b(a.base, results, a.pid)
    print(f"[B] hammer over {nfast} fast routes")
    for r in rows:
        print("   conc={concurrency:<3} rps={rps:7.1f} p50={p50_ms:7.1f} p95={p95_ms:7.1f} p99={p99_ms:7.1f} err={errors} rss={rss_mb_before}->{rss_mb_after}".format(**{k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()}))
    static = [] if a.skip_static else phase_c(a.base, a.assets.split(","))
    for s in static:
        print("[C]", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in s.items()})
    json.dump({"base": a.base, "when": time.strftime("%Y-%m-%dT%H:%M:%S"), "openapi_paths": npaths, "phase_a": results,
               "uncovered": uncovered, "phase_b": rows, "phase_c": static, "elapsed_s": time.time() - t0},
              open(a.out, "w", encoding="utf-8"), indent=1, default=str)
    print(f"wrote {a.out}  elapsed {time.time()-t0:.1f}s")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

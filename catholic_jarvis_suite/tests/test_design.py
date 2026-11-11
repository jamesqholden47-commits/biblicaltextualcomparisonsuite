"""
Phase 0 shell + design-system tests (SUITE_OVERHAUL_PLAN_2026-10-07, Claude GUI, Opus 5.5).

Each guard has a falsification case: a sample that must make the detector fire, so the check can fail.
  1. No module script hard-codes a hex colour (they use jarvis.css tokens).
  2. Every var(--token) a module or the shell uses is defined in jarvis.css or index.html :root.
  3. Every tab on the page (built-in buttons + module manifest) belongs to a workspace in shell.js,
     so the new sidebar can never hide a feature.
  4. /api/build_info reports code changed after the server started (and nothing when nothing changed).
  5. /api/books/search finds chapters by title words and returns nothing for nonsense.
"""
import json
import os
import re
import sys
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
STATIC = os.path.join(APP_DIR, "static")
MODULES = os.path.join(STATIC, "modules")

# a hex colour in a CSS-ish position: after ":" or a quote or whitespace, not inside an href="#..." anchor
HEX = re.compile(r"""(?<![\w&])(?<!href=")(?<!href=')#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_-])""")
VAR = re.compile(r"var\(--([a-z0-9-]+)")
DEFINED = re.compile(r"--([a-z0-9-]+)\s*:")


def _read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def _strip_comments(js):
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", "", js)


# A canvas cannot draw with var(--token), so canvas code reads the token and keeps a hex only as the fallback if the
# lookup fails: getCssColor("--accent-gold", "#d4af37"). That follows the rule; it is not a hard-coded colour.
# (2026-10-13: navigator.js did exactly this and the old check failed it: a check that fails when nothing is wrong.)
TOKEN_FALLBACK = re.compile(r"""getCssColor\(\s*[^,()]+,\s*["']#[0-9a-fA-F]{3,6}["']\s*\)""")


def hex_colours(js):
    return HEX.findall(TOKEN_FALLBACK.sub("getCssColor(token)", _strip_comments(js)))


def shell_tab_ids(shell_js):
    block = shell_js[shell_js.index("var WORKSPACES"):shell_js.index("var TAB_TO_WS")]
    if "var RETIRED" in block:
        block = block[:block.index("var RETIRED")]
    return set(re.findall(r'\["([a-z0-9_]+)",\s*"', block))


def retired_ids(shell_js):
    """Retired tab -> its new home (Phase 5)."""
    m = re.search(r"var RETIRED = \{([^}]*)\}", shell_js)
    return dict(re.findall(r'(\w+):\s*"([a-z0-9_]+)"', m.group(1))) if m else {}


def page_tab_ids():
    html = _read(os.path.join(STATIC, "index.html"))
    ids = set(re.findall(r'id="btn-tab-([a-z0-9_]+)"', html))
    with open(os.path.join(MODULES, "manifest.json"), encoding="utf-8") as fh:
        ids |= {m["id"] for m in json.load(fh)}
    return ids


class TestDesignSystem(unittest.TestCase):
    def test_detector_fires_on_hex_and_spares_anchors(self):
        self.assertEqual(len(hex_colours('style: "color:#2ea44e;border:1px solid #fff"')), 2)
        self.assertEqual(len(hex_colours('x = "#0d1117";')), 1)
        self.assertEqual(hex_colours('a href="#add" id="#fed-box"'), [])
        self.assertEqual(hex_colours("// was #2ea44e\n/* #fff */ ok"), [])
        # a token lookup with a hex fallback passes; a bare hex beside it still fails
        self.assertEqual(hex_colours('var g = getCssColor("--accent-gold", "#d4af37");'), [])
        self.assertEqual(hex_colours('var g = getCssColor(b.def.colorVar, "#38bdf8"); ctx.fillStyle = "#ff0000";'), ["#ff0000"])

    def test_no_module_hardcodes_hex(self):
        bad = {}
        for f in sorted(os.listdir(MODULES)):
            if f.endswith(".js"):
                hits = hex_colours(_read(os.path.join(MODULES, f)))
                if hits:
                    bad[f] = hits[:5]
        self.assertEqual(bad, {}, "use jarvis.css tokens (var(--ok), var(--bad), ...) instead of hex colours")

    def test_every_used_token_is_defined(self):
        defined = set(DEFINED.findall(_read(os.path.join(STATIC, "jarvis.css"))))
        defined |= set(DEFINED.findall(_read(os.path.join(STATIC, "index.html"))))
        used = {}
        for f in sorted(os.listdir(MODULES)) + ["../shell.js"]:
            if f.endswith(".js"):
                for t in VAR.findall(_read(os.path.join(MODULES, f))):
                    used.setdefault(t, f)
        missing = {t: f for t, f in used.items() if t not in defined}
        self.assertEqual(missing, {})
        # falsification: an invented token must be reported
        self.assertNotIn("no-such-token-xyz", defined)


class TestShellCoverage(unittest.TestCase):
    def test_every_page_tab_is_in_a_workspace(self):
        js = _read(os.path.join(STATIC, "shell.js"))
        in_shell = shell_tab_ids(js)
        retired = retired_ids(js)
        on_page = page_tab_ids()
        self.assertGreaterEqual(len(on_page), 21)
        self.assertEqual(sorted(on_page - in_shell - set(retired)), [], "a tab missing from WORKSPACES would be unreachable")
        # a retired tab must point at a home that is itself reachable
        for old, new in retired.items():
            self.assertIn(new, in_shell & on_page, f"retired tab {old} -> {new}, which is not reachable")

    def test_coverage_check_can_fail(self):
        js = 'var WORKSPACES = [ { tabs: [["cockpit", "Horarium"]] } ];\nvar TAB_TO_WS = {};'
        self.assertEqual(shell_tab_ids(js), {"cockpit"})
        self.assertIn("anki", page_tab_ids() - shell_tab_ids(js))

    def test_index_loads_shell_and_css(self):
        html = _read(os.path.join(STATIC, "index.html"))
        self.assertIn('/static/jarvis.css', html)
        self.assertIn('/static/shell.js', html)
        self.assertLess(html.index("/static/jarvis.css"), html.index("</head>"))


class TestShellEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        import app as app_mod
        cls.app_mod = app_mod
        cls.client = TestClient(app_mod.app)

    def test_build_info_fresh_and_stale(self):
        real = self.app_mod.START_TIME
        try:
            self.app_mod.START_TIME = 4102444800          # year 2100: nothing on disk is newer
            self.assertEqual(self.client.get("/api/build_info").json()["stale"], [])
            self.app_mod.START_TIME = 0                   # 1970: every code file is newer
            stale = self.client.get("/api/build_info").json()["stale"]
            self.assertIn("app.py", stale)
            self.assertTrue(any(s.startswith("modules") for s in stale))
        finally:
            self.app_mod.START_TIME = real

    def test_books_search(self):
        r = self.client.get("/api/books/search", params={"q": "zzqqxx-nonsense"})
        if r.status_code == 503:
            self.skipTest("no Volumes plan on this machine")
        self.assertEqual(r.json()["total"], 0)
        plan = self.client.get("/api/books/summary").json()
        title = plan["volumes"][0]["title"].split()[0]
        hit = self.client.get("/api/books/search", params={"q": title}).json()
        self.assertGreater(hit["total"], 0)


if __name__ == "__main__":
    unittest.main()

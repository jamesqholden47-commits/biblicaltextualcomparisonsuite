"""CatholicJarvis feature modules.

Each feature lives in its own files, owned by one worker:
  modules/<name>_routes.py    -> must define `router` (a FastAPI APIRouter, prefix /api/<name>)
  static/modules/<name>.js    -> must register  window.JarvisModules["<name>"] = { load(el) { ... } }
  tests/test_<name>.py        -> unittest, runnable on its own

app.py auto-includes every modules/*_routes.py; index.html hosts every module tab listed in
static/modules/manifest.json. Shared, read-only for workers: modules/log_reader.py.
"""

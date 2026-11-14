"""
CATHOLICJARVIS MASTER WORK SUITE
Unified Operating Environment for Independent Theologian-Philosopher.
Combines:
  1. Daily Life Cockpit & Schedule Tracker
  2. "Pope Tools" Patristic & Philological Defeaters
  3. Anki SM-2 Spaced Repetition Engine & Exporter
  4. Auditory PDF Studio with Ava Neural Voice & Scrivener Deck
  5. Theologian Career & Monetization Blueprint
"""

import os
import re
import io
import json
import time
import hashlib
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
# edge_tts is imported where it is used (0.8 s of start-up; most sessions never read aloud). Phase 5, 2026-10-07.

app = FastAPI(title="CatholicJarvis Master Work Suite")

_raw_origins = os.environ.get("ALLOWED_ORIGINS", "").strip()
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()] if _raw_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from modules.rate_limit import RateLimitMiddleware
    if os.environ.get("PLENARY_RATE_LIMIT", "0").strip().lower() in ("1", "true", "yes"):
        app.add_middleware(RateLimitMiddleware)
except Exception as _rl_err:
    print(f"Warning: RateLimitMiddleware not loaded: {_rl_err}")


@app.get("/api/health/ready")
def health_ready():
    """Lightweight readiness probe for load balancers / Tauri / SaaS."""
    from modules.plenary_db_routes import get_db_path
    db_ok = get_db_path().is_file()
    return {"status": "ready" if db_ok else "degraded", "plenary_sqlite": db_ok}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(BASE_DIR, "audio_cache")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Mount static files so PDF Studio iframe (/static/studio_frame.html) loads properly
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

WEB_APP_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "web_app"))

# James's request (2026-11-11): "open any verse jumped to the point in its respective pdf even if
# we have to create one." Two routes:
#   /plenary/source_pdf/{key} -- for a note that really was extracted from a source PDF on disk
#   (NABRE, Ignatius CSB Genesis/Exodus), serve that exact file so the frontend can open it with a
#   '#page=N' fragment and land on the right page in the browser's own PDF viewer.
#   /plenary/note_pdf -- for every other source (EPUB/API-derived: NET, NOAB, SBL, NIV, BSB, the 7
#   HelloAO commentaries, Tyndale profiles), there is no real source PDF to jump into, so this
#   generates a minimal one-page PDF of that specific note's own text on the fly with PyMuPDF
#   (already a dependency here, used elsewhere in this file for PDF Studio) -- satisfying "even if
#   we have to create one" without inventing a fake multi-page "source volume" that never existed.
# A whitelist, not an arbitrary-path query param: this app otherwise never exposes a route that
# reads an arbitrary filesystem path named by the client, and this doesn't start now.
# Built from paths_config.get_path() roots, not hardcoded -- this project already did a whole pass
# (2026-11-11, "Hardcoded personal paths made configurable") moving every module off literal
# C:\Users\Elation\... paths for exactly this reason: a different operator pointing this suite at
# their own folders, and not leaking James's personal folder layout into the public export repo's
# source. A new feature re-hardcoding paths the same week that pass shipped would undo it.
try:
    from modules.paths_config import get_path
except ImportError:
    get_path = None

PLENARY_SOURCE_PDFS = {}
if get_path:
    PLENARY_SOURCE_PDFS = {
        # Matches web_app/build_nabre_notes.py's own NABRE_PDF_PATH exactly -- note the Unicode
        # right-single-quote (U+2019) in "Anna's Archive", not an ASCII apostrophe. A raw string
        # can't escape its own closing quote character either way, so this is built the same
        # two-piece way the extractor itself does, not copy-pasted with a `\'` that silently keeps
        # the backslash.
        'nabre': os.path.join(get_path('downloads'), (
            "The Catholic Study Bible - Third Edition (NABRE 2016) -- Donald Senior, John "
            "Collins, Mary Ann Getty -- 3, 2016 -- Oxford University Press -- "
            "060eb057dd75baca4149e947f9664dc5 -- Anna\u2019s Archive.pdf"
        )),
        # Matches build_notes_shards.py's own PDFS_IGNATIUS_DIR + filenames exactly -- Exodus's
        # real filename has no "(2011)" suffix, unlike Genesis's; caught by testing this against
        # disk rather than assuming the two filenames follow the same pattern (Rule 5).
        'ignatius_gen': os.path.join(get_path('pdfs_dir'), "01_Biblical_Studies_and_Canon",
            "_AA_ Hahn, Scott & Mitch, Curtis - The Ignatius Catholic Study Bible Genesis (2011).pdf"),
        'ignatius_exod': os.path.join(get_path('pdfs_dir'), "01_Biblical_Studies_and_Canon",
            "_AA_ Hahn, Scott & Mitch, Curtis - The Ignatius Catholic Study Bible Exodus.pdf"),
        'ignatius_sam': os.path.join(get_path('pdfs_dir'), "01_Biblical_Studies_and_Canon",
            "_AA_ Hahn, Scott, author; Mitch, Curtis; Walters, Dennis; Barber, - The first and second book of Samuel.pdf"),
        'denzinger': os.path.join(get_path('pdfs_dir'), "04_Theology_Dogma_and_Sacraments",
            "Denzinger-The-Sources-Of-Catholic-Dogma-reduced.pdf"),
        'ccc_commentary': os.path.join(get_path('pdfs_dir'), "04_Theology_Dogma_and_Sacraments",
            "CCC Official Theological Commentary (1).pdf"),
        'tanner_v1': os.path.join(get_path('pdfs_dir'), "08_Church_History_and_Councils",
            "Tanner, SJ - Decrees of the Ecumenical Councils, v. 1 OCR (1990).pdf"),
        'bellarmine_councils': os.path.join(get_path('pdfs_dir'), "08_Church_History_and_Councils",
            "Robert Bellarmine - On the Councils St Bellarmine.pdf"),
    }


@app.get("/plenary/source_pdf/{key}")
def plenary_source_pdf(key: str):
    path = PLENARY_SOURCE_PDFS.get(key)
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail=f"No source PDF registered/found for '{key}'")
    safe_name = os.path.basename(path).replace('"', "'")
    return FileResponse(
        path,
        media_type="application/pdf",
        content_disposition_type="inline",
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )


# Whitelisted Schaff ANF / NPNF Series 1 & 2 volumes (anf01..10, npnf101..114, npnf201..214)
# stored in <pdfs_dir>/02_Patristics_and_Church_Fathers/Schaff_ANF_NPNF/<vol>.pdf.
# Serves the local PDF directly so the Patristic Citation Tracker in Plenary Suite can open
# any cited Church Father's primary English translation volume in a new tab.
_SCHAFF_VOL_RE = re.compile(r'^(?:anf(?:0[1-9]|10)|npnf[12](?:0[1-9]|1[0-4]))$')


@app.get("/plenary/schaff_pdf/{vol}")
def plenary_schaff_pdf(vol: str):
    vol_clean = (vol or "").strip().lower()
    if not _SCHAFF_VOL_RE.match(vol_clean) or not get_path:
        raise HTTPException(status_code=404, detail=f"Unknown or unconfigured Schaff volume '{vol}'")
    path = os.path.join(
        get_path("pdfs_dir"),
        "02_Patristics_and_Church_Fathers",
        "Schaff_ANF_NPNF",
        f"{vol_clean}.pdf",
    )
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail=f"Schaff PDF file not found on disk for '{vol_clean}'")
    return FileResponse(
        path,
        media_type="application/pdf",
        content_disposition_type="inline",
        headers={"Content-Disposition": f'inline; filename="{vol_clean}.pdf"'},
    )


@app.get("/plenary/note_pdf")
def plenary_note_pdf(src: str = Query(...), ref: str = Query(...), title: str = Query(...), html: str = Query(...), license: str = Query("")):
    """Generates a single-page PDF of one study note on the fly -- the 'create one' fallback for
    every source that has no real PDF behind it (API/EPUB-derived commentaries). `html` is the
    note's own rendered body; tags are stripped for this plain-text rendering since PyMuPDF's
    insert_textbox takes plain text, not markup."""
    plain = re.sub(r'<[^>]+>', '', html or '').strip()
    plain = plain.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # US Letter
    margin = 54
    y = margin
    page.insert_textbox(fitz.Rect(margin, y, 612 - margin, y + 40), ref, fontsize=18, fontname="hebo", color=(0.1, 0.1, 0.4))
    y += 44
    page.insert_textbox(fitz.Rect(margin, y, 612 - margin, y + 30), title, fontsize=12, fontname="hebo", color=(0.3, 0.3, 0.3))
    y += 34
    page.insert_textbox(fitz.Rect(margin, y, 612 - margin, 792 - margin - 40), plain, fontsize=10.5, fontname="helv", color=(0, 0, 0))
    footer = f"Source: {src} — generated by Plenary Suite from its own extracted study-note text (no independent source PDF exists for this entry)."
    if license:
        footer += f" License/attribution: {license}"
    page.insert_textbox(fitz.Rect(margin, 792 - margin - 30, 612 - margin, 792 - margin), footer, fontsize=7.5, fontname="helv", color=(0.5, 0.5, 0.5))
    buf = io.BytesIO(doc.tobytes())
    doc.close()
    return Response(content=buf.getvalue(), media_type="application/pdf", headers={
        "Content-Disposition": f'inline; filename="{re.sub(r"[^A-Za-z0-9_.-]", "_", ref)}_{src}.pdf"'
    })


@app.get("/plenary/magisterial_pdf")
def plenary_magisterial_pdf(
    doc_id: str = Query("council"),
    title: str = Query("Magisterial Document"),
    citation: str = Query(""),
    kind: str = Query("Council"),
    summary: str = Query(""),
    canons: str = Query(""),
    refs: str = Query(""),
    pdf_key: str = Query(""),
):
    """Serves a local primary Magisterial source PDF inline when configured and present on disk
    (e.g., Denzinger, Tanner Councils v.1, Bellarmine On the Councils, CCC Commentary), or falls
    back cleanly to an on-the-fly structured PDF folio generated via PyMuPDF."""
    key_clean = (pdf_key or "").strip()
    if key_clean and key_clean in PLENARY_SOURCE_PDFS:
        fpath = PLENARY_SOURCE_PDFS[key_clean]
        if fpath and os.path.isfile(fpath):
            safe_name = os.path.basename(fpath).replace('"', "'")
            return FileResponse(
                fpath,
                media_type="application/pdf",
                content_disposition_type="inline",
                headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
            )

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    margin = 52
    y = margin
    page.insert_textbox(
        fitz.Rect(margin, y, 612 - margin, y + 22),
        f"MAGISTERIAL ENCHIRIDION · {kind.upper()}",
        fontsize=9.5,
        fontname="hebo",
        color=(0.65, 0.42, 0.05),
    )
    y += 22
    page.insert_textbox(
        fitz.Rect(margin, y, 612 - margin, y + 48),
        title,
        fontsize=15.5,
        fontname="hebo",
        color=(0.08, 0.14, 0.28),
    )
    y += 46
    if citation:
        page.insert_textbox(
            fitz.Rect(margin, y, 612 - margin, y + 22),
            citation,
            fontsize=9.5,
            fontname="helv",
            color=(0.35, 0.40, 0.48),
        )
        y += 24
    page.draw_line(fitz.Point(margin, y), fitz.Point(612 - margin, y), color=(0.75, 0.78, 0.84), width=0.8)
    y += 14
    sections = []
    if summary:
        sections.append(f"DOGMATIC SYNTHESIS & CONTEXT:\n{summary.strip()}")
    if canons:
        sections.append(f"KEY CANONS / THESES / CONSTITUTIONS:\n{canons.strip()}")
    if refs:
        sections.append(f"PRIMARY BIBLICAL LOCI:\n{refs.strip()}")
    body_text = "\n\n".join(sections) or title
    page.insert_textbox(
        fitz.Rect(margin, y, 612 - margin, 792 - margin - 38),
        body_text,
        fontsize=10.5,
        fontname="helv",
        color=(0.08, 0.09, 0.12),
    )
    page.insert_textbox(
        fitz.Rect(margin, 792 - margin - 26, 612 - margin, 792 - margin),
        "Generated inline by Plenary Scripture Workstation · Catholic Magisterial Apparatus",
        fontsize=7.5,
        fontname="helv",
        color=(0.48, 0.52, 0.58),
    )
    buf = io.BytesIO(doc.tobytes())
    doc.close()
    safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", doc_id or "magisterial")
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{safe_id}.pdf"'},
    )

# Plenary Logos Suite integration (2026-11-10): mounted straight from the canonical web_app/
# workstation directory rather than copying its files into static/ — the suite's own build script
# (web_app/build_plenary_logos_suite.py) regenerates plenary_logos_suite.html in place, and a copy
# here would silently drift stale the next time it rebuilds. The other legacy standalone tools
# (synoptic_manuscript_diff.html etc.) were copied into static/ in an earlier session; this mount
# is the better pattern and is used for every new cross-suite tab added from here on.
# MUST be registered AFTER the two /plenary/source_pdf and /plenary/note_pdf routes above: a
# Mount matches on its path PREFIX and, once matched, Starlette never falls through to a route
# registered later even if the sub-app (StaticFiles) itself 404s -- confirmed the hard way
# (2026-11-11): registering this mount first made both new routes unreachable, always returning
# StaticFiles' own 404 instead of either real response.
if os.path.isdir(WEB_APP_DIR):
    app.mount("/plenary", StaticFiles(directory=WEB_APP_DIR), name="plenary")
else:
    print(f"Warning: web_app directory not found at {WEB_APP_DIR} — Plenary Logos Suite tab will 404")

START_TIME = time.time()
ANKI_FILE = os.path.join(DATA_DIR, "anki_cards.json")
SCHEDULE_FILE = os.path.join(DATA_DIR, "schedule_state.json")
STUDIO_CARDS_FILE = os.path.join(DATA_DIR, "studio_cards.json")
DEFEATERS_FILE = os.path.join(DATA_DIR, "defeaters.json")
ARGUMENTS_FILE = os.path.join(DATA_DIR, "argument_register.json")
DEBATES_FILE = os.path.join(DATA_DIR, "debate_battle_cards.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "ai_session_index.json")
CONCORDANCE_FILE = os.path.join(DATA_DIR, "vault_concordance.json")
PORT_FILE = os.path.join(DATA_DIR, "port.txt")
PODCAST_DIR = os.path.join(DATA_DIR, "podcast_episodes")
os.makedirs(PODCAST_DIR, exist_ok=True)

# Include Corpus Router for real dynamic file index, full-text search, and stats
try:
    from corpus_routes import router as corpus_router
    app.include_router(corpus_router)
except ImportError as e:
    print(f"Warning: corpus_router not imported: {e}")

# Feature modules (added 2026-10-03, Claude GUI): every modules/<name>_routes.py that defines
# `router` is included. A module that fails to import is reported at /api/modules, never fatal.
import glob as _glob
import importlib as _importlib
MODULE_STATUS: Dict[str, str] = {}
for _p in sorted(_glob.glob(os.path.join(BASE_DIR, "modules", "*_routes.py"))):
    _name = os.path.basename(_p)[:-3]
    try:
        _mod = _importlib.import_module(f"modules.{_name}")
        app.include_router(_mod.router)
        MODULE_STATUS[_name] = "loaded"
    except Exception as _e:  # noqa: BLE001 — surface the failure, keep the suite up
        MODULE_STATUS[_name] = f"FAILED: {type(_e).__name__}: {_e}"
        print(f"Warning: module {_name} not loaded: {_e}")


@app.get("/api/build_info")
async def build_info():
    """When this server process started, and which code files changed on disk since (so the shell can say
    "restart to load the latest code"). Static files are served fresh on every request, so only server-side
    Python counts as stale. Added 2026-10-07 (Phase 0 shell)."""
    files = [os.path.join(BASE_DIR, "app.py"), os.path.join(BASE_DIR, "corpus_routes.py")]
    files += _glob.glob(os.path.join(BASE_DIR, "modules", "*.py"))
    stale = sorted(os.path.relpath(f, BASE_DIR) for f in files
                   if os.path.exists(f) and os.path.getmtime(f) > START_TIME + 1)
    return {"started": START_TIME, "stale": stale, "modules": MODULE_STATUS}


@app.get("/api/modules")
async def list_modules():
    manifest_path = os.path.join(STATIC_DIR, "modules", "manifest.json")
    manifest = []
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    return {"routers": MODULE_STATUS, "tabs": manifest}

# Default Anki Seed Cards from Recent Breakthroughs
INITIAL_ANKI_CARDS = [
    {
        "id": 1,
        "deck": "Patristics & Defeaters",
        "prompt": "Was the Synod of Diamper (1599) validly confirmed by Rome, and how did Rome resolve the St. Thomas Christian crisis?",
        "answer": "Diamper was an invalid diocesan synod convened unilaterally by Archbishop Menezes, NEVER confirmed in forma specifica by Rome. Pope Alexander VII bypassed the Portuguese Padroado in 1659 to consecrate native Indian bishop Palliveettil Mar Chandy (1663), and Pope Leo XIII (Orientalium Dignitas, 1894) banned Latinization under pain of suspension a divinis.",
        "citation": "Alexander VII, Brief Pro Commissa Nobis (1659); Leo XIII, Orientalium Dignitas (1894)",
        "original_text": "Orientalium Dignitas: 'Praescriptiones hasce... sub poena suspensionis a divinis... confirmamus.'",
        "defeater": "1,500 years of Nasrani isolation proves ancient apostolic Christianity was sacramental, sacerdotal, and hierarchical long before medieval European Latinization.",
        "repetition": 1,
        "interval": 1,
        "easeFactor": 2.5,
        "dueDate": time.time()
    },
    {
        "id": 2,
        "deck": "Biblical Philology",
        "prompt": "Why is 1 Chronicles 29:20 the definitive biblical defeater against the Protestant charge that bodily bowing (hishtachavah) is inherently latria/idolatry?",
        "answer": "1 Chron 29:20 employs coordinate syntax where the exact same verb (hishtachavah) and coordinate prepositions govern God and the King in the exact same breath without sin.",
        "citation": "MT & LXX 1 Chron 29:20; Ugaritic yštḥwy (root ḥwy in Hištafel stem)",
        "original_text": "וַיִּקְּדוּ וַיִּשְׁתַּחֲווּ לַיהוָה וְלַמֶּלֶךְ (vayyiqqəḏū vayyištaḥăwū la-YHWH wə-la-meleḵ / LXX: προσεκύνησαν τῷ κυρίῳ καὶ τῷ βασιλεῖ)",
        "defeater": "Physical prostration is an exterior gesture whose moral character is determined by intention and sacrifice (zevach), not by the physical angle of the spine.",
        "repetition": 1,
        "interval": 1,
        "easeFactor": 2.5,
        "dueDate": time.time()
    },
    {
        "id": 3,
        "deck": "Conciliar Dogma",
        "prompt": "Does the Second Council of Nicaea (787 AD) exclude 3D statues in favor of flat 2D icons only?",
        "answer": "No. The official Greek Definition of Faith (Horos) explicitly sanctions sacred representations in colors, pebbles, 'and in other material suitably disposed' (καὶ ἑτέρας ὕλης ἐπιτηδείως ἐχούσης), which historically and scholastically includes stone, metal, and carved wood statuary.",
        "citation": "Nicaea II, Actio VII, Mansi XIII, 377D; Thomas Aquinas, ST III q. 25 a. 3",
        "original_text": "ὁρίζομεν... ἀνατίθεσθαι τὰς τιμίας καὶ ἁγίας εἰκόνας, τὰς ἐκ χρωμάτων καὶ ψηφῖδος καὶ ἑτέρας ὕλης ἐπιτηδείως ἐχούσης...",
        "defeater": "St. Thomas explicitly applies 'motus in imaginem est motus in rem' to 'lignum sculptum vel pictum' without distinction of dimension.",
        "repetition": 1,
        "interval": 1,
        "easeFactor": 2.5,
        "dueDate": time.time()
    },
    {
        "id": 4,
        "deck": "Patristics & Archaeology",
        "prompt": "How does Canon 36 of the Council of Elvira (c. 303-306 AD) refute Protestant iconoclasm rather than support it?",
        "answer": "Canon 36 ('Placuit picturas in ecclesia esse non debere, ne quod colitur et adoratur in parietibus depingatur') was an emergency pastoral decree protecting immovable wall murals from Diocletian's desecrators and preventing pagan converts from domestic syncretism. It proves churches already possessed sacred wall murals before 300 AD.",
        "citation": "Council of Elvira, Canon 36, Mansi II, 11; Dura-Europos Baptistery (232-256 AD)",
        "original_text": "Placuit picturas in ecclesia esse non debere, ne quod colitur et adoratur in parietibus depingatur.",
        "defeater": "Archaeological discovery of Dura-Europos (232 AD) and Tertullian's Eucharistic Good Shepherd chalices (c. 200 AD) prove Christian figurative art predates Elvira.",
        "repetition": 1,
        "interval": 1,
        "easeFactor": 2.5,
        "dueDate": time.time()
    },
    {
        "id": 5,
        "deck": "Patristics & Eschatology",
        "prompt": "What was the universal Patristic and Scholastic interpretation of the 'gold streets' of the New Jerusalem (Rev 21:21)?",
        "answer": "100% unanimous allegorical and spiritual consensus: gold represents the pure charity and transparent conscience of the saints united in fellowship. Zero Fathers or Scholastics interpreted it as literal elemental mineral gold (Au). Literal mineral pavement was invented by 19th-century Dispensationalists.",
        "citation": "Victorinus of Pettau (CSEL 49:150); Augustine, De Civ. Dei XX.16; Bede (PL 93:197); Nicholas of Lyra on Rev 21:21",
        "original_text": "Ambrose Autpert: 'Non ergo ibi quaerantur metalla terrena, sed caelestes virtutes intelligantur.'",
        "defeater": "The bride is the Church (Rev 21:9-10). The city is personal, spiritual, and ecclesiological glory, not municipal celestial road construction.",
        "repetition": 1,
        "interval": 1,
        "easeFactor": 2.5,
        "dueDate": time.time()
    },
    {
        "id": 6,
        "deck": "Papal Primacy",
        "prompt": "What is the decisive historical force of the Formula of Hormisdas (519 AD)?",
        "answer": "Ending the 35-year Acacian Schism, over 250 Eastern bishops, the Patriarch of Constantinople John II, and Emperor Justin I signed Rome's unconditional profession that the Catholic religion has always been preserved immaculate in the Apostolic See.",
        "citation": "Formula Hormisdae (519 AD), CSEL 35:520-522; Denzinger 363-365",
        "original_text": "'...quia in Sede Apostolica immaculata est semper catholica servata religio.'",
        "defeater": "The entire Christian East subscribed to Roman indefectibility and supreme appellate jurisdiction as the condition of communion.",
        "repetition": 1,
        "interval": 1,
        "easeFactor": 2.5,
        "dueDate": time.time()
    }
]

# Ensure Anki cards file exists
if not os.path.exists(ANKI_FILE):
    with open(ANKI_FILE, "w", encoding="utf-8") as f:
        json.dump(INITIAL_ANKI_CARDS, f, indent=2)

def load_anki_cards() -> List[Dict[str, Any]]:
    try:
        with open(ANKI_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return INITIAL_ANKI_CARDS

def save_anki_cards(cards: List[Dict[str, Any]]):
    with open(ANKI_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2)

# Recommended voices (Ava is the project default)
RECOMMENDED_VOICES = [
    {"id": "en-US-AvaNeural", "name": "Ava (US - Session Default)", "gender": "Female", "locale": "en-US"},
    {"id": "en-US-ChristopherNeural", "name": "Christopher (US - Scholarly, Authoritative)", "gender": "Male", "locale": "en-US"},
    {"id": "en-US-JennyNeural", "name": "Jenny (US - Warm, Expressive)", "gender": "Female", "locale": "en-US"},
    {"id": "en-US-GuyNeural", "name": "Guy (US - Conversational, Clear)", "gender": "Male", "locale": "en-US"},
    {"id": "en-GB-RyanNeural", "name": "Ryan (UK - Distinguished, Academic)", "gender": "Male", "locale": "en-GB"},
    {"id": "en-GB-SoniaNeural", "name": "Sonia (UK - Elegant, Calm)", "gender": "Female", "locale": "en-GB"},
    {"id": "en-US-AriaNeural", "name": "Aria (US - Crisp, Articulate)", "gender": "Female", "locale": "en-US"},
]

# PDF text cleaning
def clean_pdf_text(raw_text: str) -> str:
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', raw_text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\.{4,}', '', text)
    return text.strip()

def chunk_text(text: str, max_words: int = 55) -> List[str]:
    raw_paras = [p.strip() for p in text.split('\n') if p.strip()]
    chunks = []
    for p in raw_paras:
        sentences = re.split(r'(?<=[.!?])\s+', p)
        current_chunk = []
        current_word_count = 0
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            words = s_clean.split()
            if current_word_count + len(words) > max_words and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [s_clean]
                current_word_count = len(words)
            else:
                current_chunk.append(s_clean)
                current_word_count += len(words)
        if current_chunk:
            chunks.append(" ".join(current_chunk))
    return chunks

# ── API ROUTES ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def get_health():
    """Real system health check for daemon status, cache, and index freshness."""
    now = time.time()
    cache_files = len(os.listdir(CACHE_DIR)) if os.path.exists(CACHE_DIR) else 0
    index_file = os.path.join(DATA_DIR, "corpus_index.json")
    index_age_s = round(now - os.path.getmtime(index_file), 1) if os.path.exists(index_file) else None
    cards = load_anki_cards()
    due_count = len([c for c in cards if c.get("dueDate", 0) <= now])
    
    port_used = 8080
    if os.path.exists(PORT_FILE):
        try:
            with open(PORT_FILE, "r") as pf:
                port_used = int(pf.read().strip())
        except Exception:
            pass

    return {
        "status": "online",
        "app": "CatholicJarvis Master Work Suite",
        "port": port_used,
        "uptime_seconds": round(now - START_TIME, 1),
        "tts_voice_default": "en-US-AvaNeural",
        "audio_cache_count": cache_files,
        "corpus_indexed": os.path.exists(index_file),
        "corpus_index_age_seconds": index_age_s,
        "anki_total_cards": len(cards),
        "anki_due_today": due_count,
        "hot_path_caches": hot_path_cache_status(),
    }


def hot_path_cache_status():
    """Reports whether each of this session's in-process (mtime, size)-keyed caches is warm --
    not a correctness surface, just operator visibility into the fixes landed 2026-11-12 for
    /api/recall/status, /api/navigator/tree + /genealogy, and /api/catalog/files, each of which
    used to re-parse a multi-MB JSON file from disk on every single request. 'warm' here means
    the FIRST request after process start has already happened and primed the in-memory copy."""
    out = {}
    try:
        from modules.recall_index import _CORPUS_FILES_CACHE
        out["recall_corpus_files"] = {"warm": _CORPUS_FILES_CACHE.get("key") is not None}
    except Exception as e:  # noqa: BLE001
        out["recall_corpus_files"] = {"warm": False, "error": str(e)}
    try:
        from modules.log_reader import _SOURCES_CACHE, _SOURCES_TTL_S
        # _SOURCES_CACHE["at"] is stamped with time.monotonic() in log_reader.py (an arbitrary
        # reference point, NOT Unix epoch) -- subtracting the wall-clock time.time() used
        # elsewhere in this function, as an earlier version of this code did, produces a
        # meaningless huge number. Must diff against monotonic() too.
        age = round(time.monotonic() - _SOURCES_CACHE["at"], 1) if _SOURCES_CACHE.get("value") is not None else None
        out["log_reader_sources"] = {"warm": _SOURCES_CACHE.get("value") is not None, "age_seconds": age, "ttl_seconds": _SOURCES_TTL_S}
    except Exception as e:  # noqa: BLE001
        out["log_reader_sources"] = {"warm": False, "error": str(e)}
    try:
        from modules.navigator_core import _SCAN_CACHE
        out["navigator_scan"] = {"warm": _SCAN_CACHE.get("key") is not None}
    except Exception as e:  # noqa: BLE001
        out["navigator_scan"] = {"warm": False, "error": str(e)}
    try:
        from modules.catalog_routes import _LOAD_CACHE
        out["catalog_files"] = {"warm": len(_LOAD_CACHE) > 0, "paths_cached": len(_LOAD_CACHE)}
    except Exception as e:  # noqa: BLE001
        out["catalog_files"] = {"warm": False, "error": str(e)}
    return out

@app.get("/api/voices")
async def get_voices():
    return RECOMMENDED_VOICES

@app.get("/api/anki")
async def get_anki():
    cards = load_anki_cards()
    now = time.time()
    due_cards = [c for c in cards if c.get("dueDate", 0) <= now]
    return {
        "total": len(cards),
        "due_count": len(due_cards),
        "cards": cards
    }

@app.post("/api/anki/distill")
async def distill_anki_from_dossiers():
    """Trigger the auto-anki distiller to parse cards from research dossiers."""
    try:
        from auto_anki_distiller import distill_and_sync
        distill_and_sync()
        cards = load_anki_cards()
        return {"status": "ok", "total_cards": len(cards), "message": "Dossiers successfully distilled into Anki deck."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/anki/add")
async def add_anki_card(payload: Dict[str, Any]):
    cards = load_anki_cards()
    new_id = max([c.get("id", 0) for c in cards] + [0]) + 1
    new_card = {
        "id": new_id,
        "deck": payload.get("deck", "General Apologetics"),
        "prompt": payload.get("prompt", "").strip(),
        "answer": payload.get("answer", "").strip(),
        "citation": payload.get("citation", "").strip(),
        "original_text": payload.get("original_text", "").strip(),
        "defeater": payload.get("defeater", "").strip(),
        "repetition": 0,
        "interval": 1,
        "easeFactor": 2.5,
        "dueDate": time.time()
    }
    cards.append(new_card)
    save_anki_cards(cards)
    return {"status": "ok", "card": new_card}

@app.post("/api/anki/review")
async def review_anki_card(payload: Dict[str, Any]):
    """SM-2 Spaced Repetition Grading: grade 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)"""
    card_id = payload.get("id")
    grade = payload.get("grade", 3)
    cards = load_anki_cards()
    card = next((c for c in cards if c["id"] == card_id), None)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    rep = card.get("repetition", 0)
    interval = card.get("interval", 1)
    ease = card.get("easeFactor", 2.5)

    if grade == 1:  # Again
        rep = 0
        interval = 1
        ease = max(1.3, ease - 0.2)
    elif grade == 2:  # Hard
        interval = max(1, int(interval * 1.2))
        ease = max(1.3, ease - 0.15)
    elif grade == 3:  # Good
        if rep == 0:
            interval = 1
        elif rep == 1:
            interval = 6
        else:
            interval = int(interval * ease)
        rep += 1
    elif grade == 4:  # Easy
        if rep == 0:
            interval = 4
        elif rep == 1:
            interval = 10
        else:
            interval = int(interval * ease * 1.3)
        ease += 0.15
        rep += 1

    card["repetition"] = rep
    card["interval"] = interval
    card["easeFactor"] = round(ease, 2)
    card["dueDate"] = time.time() + (interval * 86400)
    save_anki_cards(cards)
    return {"status": "ok", "card": card}

@app.get("/api/dossiers")
async def get_dossiers():
    """Scan and return a curated catalog of research dossiers and philosophical notes."""
    catalog = [
        {
            "id": "nasranis",
            "title": "The St. Thomas Christians (Nasranis) Empirical Control Group",
            "category": "Ecclesiology & History",
            "scripture_anchor": "Acts 1:8, Malachi 1:11",
            "patristic_anchor": "Cosmas Indicopleustes, St. Ephrem, Synod of Diamper (1599)",
            "path": "THE_EMPIRICAL_CONTROL_APOLOGETIC.md",
            "status": "Fully Synthesized [V]",
            "summary": "1,500 years of geographic isolation proves ancient apostolic Christianity was sacramental, sacerdotal, and hierarchical."
        },
        {
            "id": "hishtachavah",
            "title": "Hebrew Philology of Bowing (Hishtachavah & 1 Chron 29:20)",
            "category": "Biblical Philology",
            "scripture_anchor": "1 Chronicles 29:20, Exodus 20:4-5, Psalm 99:5",
            "patristic_anchor": "Ugaritic yštḥwy (Hištafel stem), Septuagint proskuneo",
            "path": "03_RESEARCH_DOSSIERS/THE_SACRED_PROTOTYPE_DISSERTATION.md",
            "status": "Fully Synthesized [V]",
            "summary": "Coordinate syntax in 1 Chron 29:20 proves bodily prostration is an exterior gesture governed by intent, not intrinsic latria."
        },
        {
            "id": "nicaea2_elvira",
            "title": "Iconography, Statues & Council of Elvira Canon 36",
            "category": "Patristics & Archaeology",
            "scripture_anchor": "Exodus 25:18-22, Numbers 21:8-9",
            "patristic_anchor": "Nicaea II Horos (Mansi XIII), Elvira Canon 36, Dura-Europos (232 AD)",
            "path": "03_RESEARCH_DOSSIERS/THE_SACRED_PROTOTYPE_DISSERTATION.md",
            "status": "Fully Synthesized [V]",
            "summary": "Nicaea II sanctions stone/wood sculpture under hetera hyle; Elvira Canon 36 proves church murals existed before 300 AD."
        },
        {
            "id": "gold_streets",
            "title": "Revelation 21:21 Gold Streets: Universal Patristic Consensus",
            "category": "Patristic Exegesis",
            "scripture_anchor": "Revelation 21:9-21",
            "patristic_anchor": "Victorinus of Pettau, Augustine, Bede, Nicholas of Lyra, Aquinas",
            "path": "03_RESEARCH_DOSSIERS/DOSSIER_GOLD_STREETS_METAPHOR_PATRISTIC_SCHOLASTIC",
            "status": "Fully Synthesized [V]",
            "summary": "100% unanimous diachronic consensus: gold street represents fellowship and pure charity of saints, not mineral pavement."
        },
        {
            "id": "hormisdas_primacy",
            "title": "Formula of Hormisdas (519 AD) & Roman Appellate Recourse",
            "category": "Papal Primacy",
            "scripture_anchor": "Matthew 16:18-19, Luke 22:32, John 21:15-17",
            "patristic_anchor": "Formula Hormisdae (CSEL 35), Council of Sardica Canons 3-5",
            "path": "01_MASTER_DISSERTATION/Master_Dissertation_READERS_CUT_2026-08-24.pdf",
            "status": "Fully Synthesized [V]",
            "summary": "250+ Eastern bishops and Patriarch of Constantinople confess Roman doctrinal indefectibility as the condition of communion."
        },
        {
            "id": "asar_hittar",
            "title": "Binding and Loosing (Asar ve-Hittar) & Rabbinic Continuity",
            "category": "Biblical Philology",
            "scripture_anchor": "Matthew 16:19, Matthew 18:18, Matthew 23:2-3",
            "patristic_anchor": "Mishnah, Gezirah and Takkanah juridical equivalents",
            "path": "C:/Users/Elation/aa1/11_Philosophical_Theology/Linguistic_and_Juridical_Continuity_of_the_Keys_Asar_and_Hitir.md",
            "status": "Atomic Beat [R]",
            "summary": "The Keys of Peter reflect the ancient juridical power of binding obligations and dispensing, preserved in episcopal chairs."
        },
        {
            "id": "john1_wallace",
            "title": "John 1:1c Qualitative Theos & Daniel Wallace Grammatical Audit",
            "category": "Biblical Greek Grammar",
            "scripture_anchor": "John 1:1c, Colwell's Rule",
            "patristic_anchor": "Daniel B. Wallace GGBB, Philip Harner",
            "path": "C:/Users/Elation/aa1/11_Philosophical_Theology/1. Daniel B. Wallace The Word was Qualitative God Daniel Wallace is.md",
            "status": "Atomic Beat [V]",
            "summary": "Anarthrous pre-verbal theos is qualitative-definite, proving the Logos shares God's nature without Sabellian identity."
        },
        {
            "id": "infant_baptism",
            "title": "Infant Baptism & Sprinkling/Affusion Fleet",
            "category": "Sacraments & Liturgy",
            "scripture_anchor": "Acts 2:38-39, Colossians 2:11-12, Ezekiel 36:25",
            "patristic_anchor": "Didache 7, Cyprian Epistle 69, Augustine Contra Julianum",
            "path": "03_RESEARCH_DOSSIERS/_BAPTISM_SPRINKLING_AFFUSION_DEFENSE_2026-09-28",
            "status": "Fleet Dossier [V]",
            "summary": "Affusion and infant circumcision typology verified across pre-Nicene and scholastic witnesses."
        },
        {
            "id": "purgatory_eschatology",
            "title": "Popes, Damnation & Purgatory Eschatology Fleet",
            "category": "Dogmatic Eschatology",
            "scripture_anchor": "1 Corinthians 3:12-15, 2 Maccabees 12:42-46, Matthew 12:32",
            "patristic_anchor": "Gregory the Great Dialogues IV, Council of Florence, Benedict XII",
            "path": "03_RESEARCH_DOSSIERS/_POPES_DAMNATION_PURGATORY_ESCHATOLOGY_2026-09-28",
            "status": "Fleet Dossier [V]",
            "summary": "Dogmatic boundaries of personal judgment, purgatorial cleansing fire, and historical papal caveats."
        }
    ]
    return catalog

@app.get("/api/defeaters")
async def get_defeaters():
    """Returns audited theological defeater cards with [V]/[R]/[S] provenance tags."""
    if os.path.exists(DEFEATERS_FILE):
        try:
            with open(DEFEATERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

@app.get("/api/arguments")
async def get_arguments():
    """Returns master register of arguments across the research corpus."""
    if os.path.exists(ARGUMENTS_FILE):
        try:
            with open(ARGUMENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

@app.get("/api/debates")
async def get_debates(
    front: Optional[str] = Query(None, description="Filter by theological front"),
    search: Optional[str] = Query(None, description="Search keyword in debate cards")
):
    """
    Returns tactical live debate battle cards (Protestant, Eastern Orthodox, Sedevacantist, Skeptic).
    Each card carries Concession, Fatal Counter-Fact, Source Locator, 15s Verbal Soundbite, and Copy-Paste text.
    """
    if not os.path.exists(DEBATES_FILE):
        return {"total": 0, "fronts": [], "cards": []}
    try:
        with open(DEBATES_FILE, "r", encoding="utf-8") as f:
            cards = json.load(f)
    except Exception:
        cards = []

    fronts = sorted(list({c.get("front", "General") for c in cards}))

    if front and front.strip():
        f_lower = front.strip().lower()
        cards = [c for c in cards if f_lower in c.get("front", "").lower()]

    if search and search.strip():
        s_lower = search.strip().lower()
        cards = [
            c for c in cards
            if s_lower in c.get("topic", "").lower()
            or s_lower in c.get("target", "").lower()
            or s_lower in c.get("charge", "").lower()
            or s_lower in c.get("fatal_counter_fact", "").lower()
            or s_lower in c.get("verbal_soundbite_15s", "").lower()
            or s_lower in c.get("proof_text", "").lower()
        ]

    return {
        "total": len(cards),
        "fronts": fronts,
        "cards": cards
    }

@app.get("/api/sessions")
async def get_sessions(
    surface: Optional[str] = Query(None, description="Filter by surface (antigravity / claude_transcripts)"),
    query: Optional[str] = Query(None, description="Search sessions by topic, keyword, or filename"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=100, description="Items per page")
):
    """
    Returns indexed historical AI research sessions across Antigravity and Claude CLI/GUI.
    Enables instant session discovery without multi-megabyte context bloat.
    """
    if not os.path.exists(SESSIONS_FILE):
        return {
            "total_sessions": 0,
            "total_words": 0,
            "page": page,
            "limit": limit,
            "total_pages": 0,
            "sessions": []
        }
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    all_sessions = data.get("sessions", [])
    total_words = data.get("total_words", 0)
    platforms = {}
    for s in all_sessions:
        plat = s.get("platform", "Unknown")
        platforms[plat] = platforms.get(plat, 0) + 1

    filtered = all_sessions
    if surface and surface.strip():
        s_lower = surface.strip().lower()
        filtered = [s for s in filtered if s_lower in s.get("platform", "").lower()]

    if query and query.strip():
        q_lower = query.strip().lower()
        filtered = [
            s for s in filtered
            if q_lower in s.get("title", "").lower()
            or q_lower in s.get("first_prompt", "").lower()
            or any(q_lower in str(top).lower() for top in s.get("topics", []))
            or any(q_lower in (a.get("name", "") if isinstance(a, dict) else str(a)).lower() for a in s.get("artifacts", []))
        ]

    total_filtered = len(filtered)
    total_pages = max(1, (total_filtered + limit - 1) // limit)
    start_idx = (page - 1) * limit
    page_items = filtered[start_idx : start_idx + limit]

    return {
        "total_sessions": total_filtered,
        "unfiltered_total": len(all_sessions),
        "total_words": total_words,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "platforms": platforms,
        "top_topics": data.get("top_topics", [])[:20],
        "sessions": page_items
    }

_CONC = {"mtime": None, "data": None}


def _concordance_cached():
    """The 45 MB concordance, parsed once and kept until the file changes (it was re-read on every request).
    Phase 5, 2026-10-07."""
    m = os.path.getmtime(CONCORDANCE_FILE)
    if _CONC["mtime"] != m:
        with open(CONCORDANCE_FILE, "r", encoding="utf-8") as f:
            _CONC["data"] = json.load(f)
        _CONC["mtime"] = m
    return _CONC["data"]


@app.get("/api/vaults/concordance")
async def get_vault_concordance(
    view: str = Query("summary", description="summary | clusters | drift | unique"),
    search: Optional[str] = Query(None, description="Search by title or filename"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100)
):
    """
    Returns Obsidian vault deduplication and L3 concordance intelligence.
    Identifies exact duplicate clusters across active vaults and backup clones,
    quantifying token waste and displaying canonical file locations.
    """
    if not os.path.exists(CONCORDANCE_FILE):
        return {
            "status": "indexing",
            "message": "Vault deduplication scan is running or not yet generated.",
            "total_files_scanned": 0,
            "duplicate_clusters_count": 0
        }
    try:
        data = _concordance_cached()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read concordance data: {str(e)}")

    summary = {
        "generated_at": data.get("generated_at"),
        "scan_duration_seconds": data.get("scan_duration_seconds"),
        "total_files_scanned": data.get("total_files_scanned"),
        "total_unique_documents": data.get("total_unique_documents"),
        "duplicate_clusters_count": data.get("duplicate_clusters_count"),
        "total_duplicate_copies": data.get("total_duplicate_copies"),
        "redundant_bytes_wasted": data.get("redundant_bytes_wasted"),
        "redundant_words_wasted": data.get("redundant_words_wasted"),
        "vault_breakdown": data.get("vault_breakdown", {}),
        "version_drift_files_count": data.get("version_drift_files_count", 0)
    }

    if view == "summary":
        return {
            "status": "ready",
            "summary": summary,
            "top_clusters": data.get("exact_duplicate_clusters", [])[:10],
            "top_drift": data.get("version_drift_files", [])[:10]
        }

    items = []
    if view == "clusters":
        items = data.get("exact_duplicate_clusters", [])
        if search:
            s_low = search.lower()
            items = [c for c in items if s_low in c.get("title", "").lower() or s_low in c.get("canonical", {}).get("filename", "").lower()]
    elif view == "drift":
        items = data.get("version_drift_files", [])
        if search:
            s_low = search.lower()
            items = [d for d in items if s_low in d.get("filename", "").lower()]
    elif view == "unique":
        items = data.get("unique_documents", [])
        if search:
            s_low = search.lower()
            items = [u for u in items if s_low in u.get("title", "").lower() or s_low in u.get("filename", "").lower()]

    total_items = len(items)
    total_pages = max(1, (total_items + limit - 1) // limit)
    start_idx = (page - 1) * limit
    paged = items[start_idx : start_idx + limit]

    return {
        "status": "ready",
        "view": view,
        "summary": summary,
        "total_items": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "items": paged
    }


def load_studio_cards() -> List[Dict[str, Any]]:
    if os.path.exists(STUDIO_CARDS_FILE):
        try:
            with open(STUDIO_CARDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_studio_cards(cards: List[Dict[str, Any]]):
    with open(STUDIO_CARDS_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2, ensure_ascii=False)

@app.get("/api/studio/cards")
async def get_studio_cards():
    """Retrieve saved Scrivener-style corkboard index cards."""
    return load_studio_cards()

@app.post("/api/studio/cards")
async def save_studio_cards_route(payload: List[Dict[str, Any]]):
    """Save corkboard cards server-side to data/studio_cards.json."""
    save_studio_cards(payload)
    return {"status": "ok", "total": len(payload)}

@app.post("/api/studio/cards/to_anki")
async def send_studio_card_to_anki(payload: Dict[str, Any]):
    """Convert a corkboard clipping into an active recall Anki card."""
    cards = load_anki_cards()
    new_id = max([c.get("id", 0) for c in cards] + [0]) + 1
    card_title = payload.get("title", "Studio Clipped Note").strip()
    card_text = payload.get("text", "").strip()
    doc_title = payload.get("doc_title", "").strip()
    page_num = payload.get("page", "")

    citation = f"{doc_title}, Page {page_num}" if doc_title else f"Studio Clipping (Page {page_num})"
    new_card = {
        "id": new_id,
        "deck": payload.get("deck", "PDF Studio Research"),
        "prompt": f"Patristic/Scholastic Citation: {card_title}",
        "answer": card_text,
        "citation": citation,
        "original_text": card_text,
        "defeater": f"Primary source text extracted hands-free via Auditory PDF Studio.",
        "provenance_tag": "[V]",
        "repetition": 0,
        "interval": 1,
        "easeFactor": 2.5,
        "dueDate": time.time()
    }
    cards.append(new_card)
    save_anki_cards(cards)
    return {"status": "ok", "card": new_card}

@app.get("/api/anki/export")
async def export_anki_tsv():
    """
    Export cards to TSV formatted for 1-click import into Anki desktop or AnkiMobile.
    Includes official Anki comment directives: #separator:tab and #html:true.
    """
    cards = load_anki_cards()
    lines = [
        "#separator:tab",
        "#html:true",
        "#deck column:1",
        "#tags column:7",
        "# Deck\tPrompt\tAnswer\tCitation\tOriginalText\tDefeater\tTags"
    ]
    for c in cards:
        deck_name = c.get("deck", "Default")
        front = c.get("prompt", "").replace("\t", " ").replace("\n", "<br>")
        back = (
            f"<strong>{c.get('answer', '')}</strong><br><br>"
            f"<em>Citation:</em> {c.get('citation', '')}<br>"
            f"<em>Original Text:</em> <code>{c.get('original_text', '')}</code><br><br>"
            f"<strong>Defeater:</strong> {c.get('defeater', '')}"
        ).replace("\t", " ").replace("\n", " ")
        citation = c.get("citation", "").replace("\t", " ")
        orig = c.get("original_text", "").replace("\t", " ")
        defeater = c.get("defeater", "").replace("\t", " ")
        tag = c.get("provenance_tag", "[V]")
        lines.append(f"{deck_name}\t{front}\t{back}\t{citation}\t{orig}\t{defeater}\t{tag}")
    return PlainTextResponse(content="\n".join(lines), media_type="text/tab-separated-values")

@app.get("/api/schedule")
async def get_schedule():
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Default schedule template
    return {
        "date": time.strftime("%Y-%m-%d"),
        "habits": {
            "liturgy_of_hours": False,
            "hydration_movement": False,
            "anki_queue_cleared": False,
            "deep_work_dissertation": False,
            "career_asset_shipped": False,
            "evening_examen": False
        },
        "daily_breakthrough": "Defend Nasranis empirical control group and synthesize hishtachavah syntax in dissertation."
    }

@app.post("/api/schedule")
async def save_schedule(payload: Dict[str, Any]):
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return {"status": "ok"}

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")
        doc_title = file.filename
        if doc.metadata and doc.metadata.get("title"):
            doc_title = doc.metadata.get("title")

        pages_data = []
        global_chunk_id = 0
        for page_idx in range(len(doc)):
            page_text = doc[page_idx].get_text("text")
            cleaned = clean_pdf_text(page_text)
            if not cleaned or len(cleaned) < 15:
                continue
            chunks = chunk_text(cleaned)
            page_chunks = []
            for c in chunks:
                if len(c.strip()) > 10:
                    page_chunks.append({
                        "id": global_chunk_id,
                        "page": page_idx + 1,
                        "text": c.strip()
                    })
                    global_chunk_id += 1
            if page_chunks:
                pages_data.append({
                    "page_num": page_idx + 1,
                    "chunks": page_chunks
                })
        return {
            "title": doc_title,
            "filename": file.filename,
            "total_pages": len(doc),
            "readable_pages": len(pages_data),
            "total_chunks": global_chunk_id,
            "pages": pages_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process PDF: {str(e)}")

@app.get("/api/sample")
async def get_sample():
    sample_path = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\01_MASTER_DISSERTATION\Master_Dissertation_READERS_CUT_2026-08-24.pdf"
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample PDF not found")
    doc = fitz.open(sample_path)
    pages_data = []
    global_chunk_id = 0
    for page_idx in range(min(25, len(doc))):
        page_text = doc[page_idx].get_text("text")
        cleaned = clean_pdf_text(page_text)
        if not cleaned or len(cleaned) < 15:
            continue
        chunks = chunk_text(cleaned)
        page_chunks = []
        for c in chunks:
            if len(c.strip()) > 10:
                page_chunks.append({
                    "id": global_chunk_id,
                    "page": page_idx + 1,
                    "text": c.strip()
                })
                global_chunk_id += 1
        if page_chunks:
            pages_data.append({
                "page_num": page_idx + 1,
                "chunks": page_chunks
            })
    return {
        "title": "Master Dissertation (Reader's Cut)",
        "filename": os.path.basename(sample_path),
        "total_pages": len(doc),
        "readable_pages": len(pages_data),
        "total_chunks": global_chunk_id,
        "pages": pages_data
    }

@app.get("/api/tts")
async def stream_tts(
    text: str = Query(..., description="Text to speak"),
    voice: str = Query("en-US-AvaNeural", description="Voice ID"),
    rate: str = Query("+0%", description="Speech rate")
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    key_str = f"{voice}_{rate}_{text.strip()}"
    cache_hash = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{cache_hash}.mp3")

    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            audio_bytes = f.read()
        return Response(content=audio_bytes, media_type="audio/mpeg")

    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        audio_bytes = audio_stream.getvalue()
        try:
            with open(cache_path, "wb") as f:
                f.write(audio_bytes)
        except Exception:
            pass
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

# ==============================================================================
# 10. OPENNOTEBOOKLM DEEP DIVE PODCAST SUITE
# ==============================================================================

@app.get("/api/podcast/episodes")
async def list_podcast_episodes():
    episodes = []
    if os.path.exists(PODCAST_DIR):
        for fname in sorted(os.listdir(PODCAST_DIR)):
            # Sidecars (e.g. <episode>.fidelity_reviewed.json) are not episodes.
            if fname.endswith(".json") and fname.count(".") == 1:
                fpath = os.path.join(PODCAST_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    ep_id = fname[:-5]
                    episodes.append({
                        "id": ep_id,
                        "title": meta.get("title", ep_id),
                        "subtitle": meta.get("subtitle", ""),
                        "source_document": meta.get("source_document", ""),
                        "duration": meta.get("duration_formatted", ""),
                        "total_duration_seconds": meta.get("total_duration_seconds", 0),
                        "total_turns": meta.get("total_turns", 0),
                        "speakers": meta.get("speakers", []),
                        "audio_url": f"/api/podcast/audio/{ep_id}",
                        "transcript_url": f"/api/podcast/transcript/{ep_id}"
                    })
                except Exception as e:
                    print(f"Error reading podcast episode {fname}: {e}")
    return {"episodes": episodes}

@app.get("/api/podcast/transcript/{episode_id}")
async def get_podcast_transcript(episode_id: str):
    clean_id = re.sub(r'[^a-zA-Z0-9_\-]', '', episode_id)
    json_path = os.path.join(PODCAST_DIR, f"{clean_id}.json")
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Podcast episode not found")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@app.get("/api/podcast/audio/{episode_id}")
async def get_podcast_audio(episode_id: str):
    clean_id = re.sub(r'[^a-zA-Z0-9_\-]', '', episode_id)
    audio_path = os.path.join(PODCAST_DIR, f"{clean_id}.mp3")
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="{clean_id}.mp3"',
            "Accept-Ranges": "bytes"
        }
    )

@app.route("/", methods=["GET", "HEAD"])
async def serve_index(request=None):
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h3>CatholicJarvis Work Suite: static/index.html loading...</h3>")

if __name__ == "__main__":
    import uvicorn
    import argparse
    import socket

    parser = argparse.ArgumentParser(description="CatholicJarvis Master Work Suite")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind server")
    args = parser.parse_args()

    active_port = args.port
    try:
        with open(PORT_FILE, "w", encoding="utf-8") as pf:
            pf.write(str(active_port))
    except Exception:
        pass

    print(f"[CatholicJarvis Suite] Starting on dual-stack IPv4/IPv6 port {active_port} ...")
    print(f"  • Localhost (IPv6): http://localhost:{active_port}")
    print(f"  • Loopback (IPv4):  http://127.0.0.1:{active_port}")

    # Bind true dual-stack socket (supporting both IPv4 127.0.0.1 and IPv6 ::1 localhost)
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        sock.bind(("::", active_port))
        sock.listen(128)
        config = uvicorn.Config("app:app", log_level="info")
        server = uvicorn.Server(config)
        server.run(sockets=[sock])
    except Exception as e:
        print(f"[Warning] Dual-stack bind failed ({e}), falling back to 0.0.0.0...")
        uvicorn.run("app:app", host="0.0.0.0", port=active_port, reload=False)

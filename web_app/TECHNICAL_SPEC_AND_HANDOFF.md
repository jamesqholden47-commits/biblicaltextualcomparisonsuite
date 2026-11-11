# Plenary Logos Suite — Technical Specification & Multi-Harness Handoff (`v2.0 → v3.0`)

**Canonical Workstation Root:** `C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\web_app`  
**Legacy / Brother App (Catholic Jarvis):** `C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\09_APPS_CATHOLICJARVIS\catholic_jarvis_suite`  
**Verified Baseline Date:** `2026-11-10` · **Target Audience:** Gemini Argon and any downstream engineering AI harness picking up work on James's low-token budget (~12% remaining).

---

## 0. Mandatory Project Methodological Guardrails (Non-Negotiable)
Every AI harness touching files in this repository must enforce the standing rules in `CLAUDE.md` and `GEMINI.md`:
1. **Plain English (Foreword & Rule 0):** Lead with direct facts; no cryptic shorthand or filler prose. Every claim carries `[V]` (verified in a named file/command output), `[R]` (single source), or `[S]` (proposal/inference).
2. **Never Delete Source Files (Rule 6):** Never delete `web_app/CPDV.json`, `web_app/sources_cache/*`, PDFs, or EPUBs. Only exclude unapproved texts from active builds unless explicitly overridden.
3. **Never Modify the Master Dissertation (Rule 13 & Scope Boundary):** Keep all workstation/app builds strictly inside `web_app/` (or `09_APPS_CATHOLICJARVIS/` if integrating). Do not edit `01_MASTER_DISSERTATION/`.
4. **Canonical Scope vs. Text-Type Split (Rule 20):** Never conflate **Axis A** (extra books/chapters outside the Protestant 66-book canon, e.g., Tobit–2 Maccabees, Daniel 3/13–14, Esther Additions A–F) with **Axis B** (textual variants within shared books, e.g., LXX vs. MT vs. DSS vs. Byzantine vs. Critical GNT vs. Vulgate). Keep them separated in data schemas and UI labels.
5. **Strict Offline & CSS Parity (Rule 3):** `plenary_logos_suite.html` must have **0 external CDN requests** (`<script src="http...">` / `<link href="http...">`) and **0 uncompiled Tailwind classes** relative to `web_app/tailwind_compiled.css`. If you introduce new CSS classes, either use custom `.suite-*` rules in `<style>` or rebuild `tailwind_compiled.css`.

---

## 1. Current Verified Production Architecture (`v2.0`)

### 1.1 Core Files & Exact Sizes on Disk `[V]`
| File Path (`web_app\`) | Size | Role |
|---|---:|---|
| `logos_suite_template.html` | `221,023 B` | HTML shell, CSS styles (`.suite-*`), Three.js 3D engine, Russian Doll/Parallel/Chapter reader, BibleHub Inspector, Concordance & Search modals |
| `build_plenary_logos_suite.py` | `140,601 B` | Deterministic Python compiler: merges 12 Bible corpora + lexicons + morphology + alignment + cruxes + cross-refs into `plenary_logos_data.json` and inlines everything into `plenary_logos_suite.html` |
| `ingest_approved_corpus.py` | `30,889 B` | Downloads/caches raw XML/VPL/JSON/HTML/STEPBible sources into `sources_cache/raw/` and normalizes 73-book alignment (`align_mt_to_catholic_chapters`) |
| `parse_ignatius_rsv2ce.py` | `34,479 B` | Extracts 45 born-digital books of Ignatius RSV-2CE (27 NT EPUB + 16 OT EPUBs + Gen/Exod born-digital PDFs) into `sources_cache/RSV2CE.json` |
| `build_lexicon_data.py` | `10,896 B` | Builds `sources_cache/lexicon_bundle.json` (`7,346,474 B`: 14,197 Strong's, 52,220 Greek morph keys, 42,637 Hebrew morph keys) + `dra_strongs_links.json` (`4,445,992 B`: 29,588 verse mappings) |
| `plenary_logos_data.json` | `60,913,055 B` | Compiled offline JSON database (`73` books, `12` streams) |
| `plenary_logos_suite.html` | `62,118,578 B` | Self-contained single-file deliverable (inlines `three.min.js` `603 KB`, `lucide.min.js` `355 KB`, `tailwind_compiled.css` `22.6 KB`, and `APP_DATA` JSON) |
| `tailwind_compiled.css` | `22,590 B` | Precompiled Tailwind utility CSS (`266` verified classes in current template) |
| `three.min.js` / `lucide.min.js` | `603,445 B` / `354,775 B` | Offline WebGL + UI icon libraries |

### 1.2 In-Memory `APP_DATA` Schema & Payload Breakdown `[V]`
- `canon_schema` (`6` divisions, `9,951 B`): Canonical 73-book Catholic ordering (`Pentateuch` through `Apocalypse`), metadata (`id`, `name`, `abbr`, `lxx_num`, `lang`, `deuterocanon`).
- `translation_registry` (`12` entries, `4,662 B`): Ordered stream definitions (`id`, `short`, `name`, `lang`, `scope`, `approval`, `tier_badge`, `group`, `color`, `default_3d`, `is_master_en`, `notes`):
  1. `dra` (`IMPRIMATUR`, 73b, default Master English, `35,811` verses)
  2. `rsv2ce` (`IMPRIMATUR [IN-HOUSE]`, 45b, explicit amber `DRA` fallback on uncovered books)
  3. `nova_vulg` (`PAPAL EDITIO TYPICA`, 73b, embeds Esther Additions `[1a]–[10a]`)
  4. `vulg_clem` (`PAPAL/TRENT STANDARD`, 73b, `35,817` verses)
  5. `lxx_gnt` (`ANCIENT MSS`, 73b: Rahlfs 1935 LXX + Esther A–F + StatRes Critical GNT, `35,161` verses, with GNT-only vs GNT+Byz RP omissions and Acts 19:41 / 2 Cor 13:14 versification splits separated)
  6. `byz` (`ANCIENT MSS (BYZ NT)`, 27 NT books)
  7. `tr` (`TRADITIONAL NT`, 27 NT books)
  8. `wlc` (`MASORETIC MT`, 39 protocanonical OT books, `23,213` verses)
  9. `brenton` (`LXX BENCHMARK`, 46b)
  10. `webc` (`ECUMENICAL BENCHMARK`, 73b)
  11. `kjva` (`HISTORICAL BENCHMARK`, 73b)
  12. `asv` (`66-BOOK BENCHMARK`, 66b)
- `books` (`73` items, `42,210,890 B`): Each book holds:
  - `id, name, abbr, division, testament, lang, deuterocanon, chapter_count`
  - `chap_notes{ "1": "..." }` (per-chapter witness, omission, or versification notes)
  - `verses_en[][]`, `verses_la[][]`, `verses_gr[][]`, `verses_he[][]` (0-indexed chapter, 0-indexed verse)
  - `tr{ rsv2ce, nova_vulg, webc, brenton, kjva, asv, byz?, tr? }`
- **Apparatus & Lexicon Payload (`~9.9 MB` total):** `preloaded_cruxes` (`22`, `67 KB`), `greek_morph` (`52,220` forms, `1.42 MB`), `hebrew_morph` (`42,637` forms, `2.69 MB`), `strongs_gloss` (`14,197` entries, `2.34 MB`), `latin_lex` (`64`, `3.2 KB`), `dra_links` (`29,588` verse token-Strong's maps, `3.50 MB`), `cross_refs` (`25`, `6.3 KB`).

### 1.3 Crucial Architecture Constraint (`>62 MB` Scaling Ceiling)
`plenary_logos_suite.html` is **already `62.1 MB`** because `plenary_logos_data.json` sits inline in `<script>const APP_DATA = ...;</script>`.
- Adding **translation text only** (`BSB` `~4.3 MB` + `NET21` `~4.5 MB`) brings inline HTML to **`~71 MB`**, which Chrome parses cleanly.
- **Do NOT inline full multi-bible footnotes & study commentaries** (NET's `tn/tc/sn` notes, Ignatius NT `8,396` `<sup` notes + 18 OT volumes, NIV Study Bible `124.9 MB` EPUB, SBL Study Bible `21.0 MB` EPUB, NOAB `13.2 MB` EPUB) inside `plenary_logos_suite.html`! Inlining `100–250 MB` of study prose into one HTML file causes slow startup and renderer memory pressure.
- **Recommended Solution — Dual-Mode Lazy Shard Architecture:**
  1. **Offline `file://`-Safe JSONP Shards:** Generate `web_app/notes_shards/<book_id>.js` (one file per book, `73` small files, e.g., `notes_shards/john.js`) calling `window.__PLENARY_LOAD_BOOK_NOTES('john', {...})`. Dynamic `<script src="notes_shards/john.js">` loads **both over `file://` (double-click HTML, zero CORS blocks) AND HTTP**, keeping initial HTML lean (`~65–72 MB`) while unlocking unlimited study-Bible commentary!
  2. **Catholic Jarvis Local Server Mode (`09_APPS_CATHOLICJARVIS/catholic_jarvis_suite/app.py`):** Optionally serve `/api/notes/<book>/<ch>/<v>` and `/api/study_profile` from SQLite/FTS5 when launched inside Catholic Jarvis (`Desktop\Catholic Jarvis.lnk`).

---

## 2. Verified On-Disk Asset Inventory for Phase 3 Expansion

### 2.1 Fast Text & Footnote Targets Already in `C:\Users\Elation\Downloads\` `[V]`
| Asset | Verified Path & Size | Internal Format & Parsing Recipe |
|---|---|---|
| **BSB (Berean Standard Bible)** | `Downloads\bsb.txt` (`4,331,393 B`) | Clean UTF-8 tab-separated verse table (`31,102` protocanonical verses: `Genesis 1:1\tIn the beginning...` → `Revelation 22:21`). Run through `align_mt_to_catholic_chapters()` for Psalms / Joel / Malachi Catholic chapter alignment. *(No separate BSB footnote/interlinear table file exists in Downloads yet — only verse text unless biblos tables are downloaded later.)* |
| **NET Bible 2.1 + Full `tn`/`tc`/`sn` Notes** | `Downloads\NETBIBLE21.epub` (`10,533,574 B`) + `1-NET-SAMPLER-Translation-FINAL.pdf` (`1,832,349 B`) | ZIP EPUB with `2,527` entries: **`1,255` chapter XHTMLs paired 1:1 with `1,255` `OEBPS/file*_notes.xhtml` files**. Verse anchors (`<sup><a id="n4100851" href="file1007_notes.xhtml#n4100851">51</a></sup>`) map directly to `<p id="n...">` note blocks explicitly typed `<b>tn</b>` (Translator Note), `<b>tc</b>` (Text-Critical Note), and `<b>sn</b>` (Study Note)! Align 66 books via `align_mt_to_catholic_chapters()`. |
| **NIV Study Bible (Fully Revised)** | `Downloads\NIV Study Bible, Fully Revised ... .epub` (`124,897,349 B`) | `407` XHTMLs (`OEBPS/hcp-nivsb20-*.xhtml`) using `<div class="endnote"><p class="en" id="x...">` and `<a class="xbr" href="...#v24019007">` verse IDs (`BBCCCVVV` 8-digit convention: book `24` ch `019` v `007`). Huge study notes + articles + images (`~965` ZIP entries; strip/skip heavy images during text shard extraction). |
| **SBL Study Bible (NRSVue, 2023)** | `Downloads\The SBL Study Bible_ Fully Revised ... .epub` (`20,999,801 B`) | `389` XHTMLs (`OEBPS/hcp-nrsvuesblstbib-*.xhtml`) with commentary anchors `<span class="bcv" id="com02001007">` linked to `<a class="xbr" href="...#v02001007">` (`BBCCCVVV`). Includes Deuterocanon/Apocrypha! |
| **New Oxford Annotated Bible (NRSV 6th ed., 2026)** | `Downloads\The New Oxford Annotated Bible_ New Revised Standard Version ... 2026 ... .epub` (`13,167,054 B`) | `116` XHTMLs (`OEBPS/Ch*_Coogan_Bible.xhtml`), `koboSpan`-wrapped text + `<div class="notegroup"><div class="note" id="...chapter-N-note-M">` keyed to verse markers `<b>2.12</b>`. Full 73-book Apocrypha/Deuterocanonical notes! |

### 2.2 Ignatius Catholic Study Bible & Academic Library (`C:\Users\Elation\PDFS\`) `[V]`
| Scope | Verified Files (`01_Biblical_Studies_and_Canon\` & `02_Patristics_and_Church_Fathers\`) | Note Extraction Strategy |
|---|---|---|
| **Ignatius NT (Complete 27 Books)** | `_AA_ Curtis Mitch & Scott Hahn - Ignatius Catholic Study Bible New Testament (2009).epub` (`2,390,635 B`, `page-1.html` `5.82 MB` with **`8,396` `<sup` note links**) + PDF (`14,179,437 B`, `1,621 pp`) | **High-value quick win:** Parse chapter headers + verse-keyed study notes (`n.*`) directly from `OEBPS/page-1.html` (reuse book/chapter split logic in `parse_ignatius_rsv2ce.py`). |
| **Ignatius OT Born-Digital EPUBs (16 Books)** | Separate single/paired EPUBs: `Deuteronomy`, `Joshua`, `Judges & Ruth`, `1 & 2 Kings`, `Tobit/Judith/Esther`, `Proverbs/Eccl/Song`, `Isaiah`, `Daniel`, `1 & 2 Maccabees` | Each EPUB has dedicated `href="*note*"` / `<a id="noteb...">` footnote & commentary sections cleanly parseable with BeautifulSoup/lxml. |
| **Ignatius OT Born-Digital PDFs (2 Books)** | `Genesis` (`2.57 MB`, `226 pp`), `Exodus` (`2.34 MB`, `189 pp`) | PyMuPDF (`fitz`) font-size / column-split parser (bottom commentary blocks vs top Scripture block + word-study callout boxes). |
| **Ignatius OT OCR-Layered PDFs (3 Books)** | `1 & 2 Samuel` (`12.98 MB`, `124 pp`, `10pp_chars=2859`), `Job` (`7.06 MB`, `76 pp`, `10pp_chars=2722`) | Extract **study notes & outlines only** (not raw Scripture text, per `parse_ignatius_rsv2ce.py`) and badge every note `[OCR-EXTRACTED — VERIFY AGAINST PAGE]`. *(Uncovered OT books like Psalms, Leviticus, Jeremiah, Ezekiel, Minor Prophets remain fallback to DRA + cross-tradition notes unless complete single-volume Ignatius Study Bible OT+NT is later supplied.)* |
| **Jewish & Secondary Study Tools** | `The Jewish Study Bible Second Edition (2014).epub` (`7.74 MB`), `Complete Jewish Study Bible.pdf` (`110.66 MB`), `_The_ Oxford annotated Mishnah...pdf` (`15.18 MB`), `BDAG Greek Lexicon` (`40.1 MB`), `Dictionary of Deities and Demons` (`45.9 MB`), `Lambdin Biblical Hebrew` (cited in `REPORT_2026-10-14` §2), `Ulrich DSS` (`60.7 MB`), `Gallagher & Meade Canon Lists` (`25.4 MB`), `Collected Works of Augustine` (`86.8 MB`), `Delphi Chrysostom` (`40.8 MB`), `Holmes Apostolic Fathers Greek/EN` (`30.5 MB`), `Tanner Decrees of Ecumenical Councils` (`38.8 MB`), `CCC Official Theological Commentary` (`159.1 MB`) | Index book/chapter citations against `(book_id, chap, verse)` to populate **Patristic & Second-Temple Study Notes** without fabricating citations (Rule 4). |

### 2.3 Legacy Work Suites Ready to Merge `[V]`
Located inside `web_app\` and `09_APPS_CATHOLICJARVIS\catholic_jarvis_suite\`:
- **Legacy Standalone Explorers (`web_app\`):**
  - `omitted_verses_explorer.html` (`181.6 KB`) + `omitted_verses_data.json` (`141.2 KB`) — forensic omitted-verse apparatus & Discord cards
  - `synoptic_manuscript_diff.html` (`31.9 KB`) — manuscript text-type diff viewer
  - `patristic_consensus_map.html` (`23.5 KB`) — Mediterranean patristic timeline/geography graph
  - `debate_defeater_tree.html` (`26.7 KB`) — Socratic / debate defeater tree cockpit
  - `deuterocanon_registry.html` (`21.4 KB`) — NT citations & deuterocanonical witness registry
  - `catholic_contributors.html` (`85.6 KB`) & `translation_explorer.html` (`71.4 KB`)
- **⚠️ Mandatory Audit Warning (`REPORT_2026-10-14` §§2, 4):** The Oct 9–13 Antigravity modules (`synoptic_manuscript_diff`, `patristic_consensus_map`, `debate_defeater_tree`, `deuterocanon_registry`) were only checked for loading without HTTP/JS errors — **their historical quotes and statistics have NOT been fact-checked.** When importing their UI widgets or datasets into the Plenary Suite or Catholic Jarvis, tag unverified rows `[S / AUDIT PENDING]` until verified against primary files on disk!
- **Brother Full-Stack Suite (`Catholic Jarvis`):** `09_APPS_CATHOLICJARVIS\catholic_jarvis_suite\app.py` (`44.6 KB`, `34` tabs across `8` workspaces, `VERBUM_LOGOS_SUITE_DESIGN_SPEC.md` `4.4 KB`). Treat Plenary Suite as the Scripture/3D/Lexicon workspace inside (or synced cleanly with) Catholic Jarvis.

---

## 3. Architectural Blueprint for Next-Phase Features (`v3.0`)

### Feature A — Multi-Translation Footnote, Translator & Study-Note Multiplexer ("Bible-Within-a-Bible Notes")
1. **Standardized Note Schema (`notes_shards/<book_id>.js`):**
   ```json
   {
     "book_id": "john",
     "chapters": {
       "1": {
         "1": [
           {
             "src": "net21",
             "tier": "PROTESTANT/CRITICAL",
             "kind": "tn",
             "marker": "1",
             "title": "tn — 'Word' (λόγος)",
             "html": "..."
           },
           {
             "src": "ignatius",
             "tier": "CATHOLIC IMPRIMATUR",
             "kind": "study",
             "marker": "1:1",
             "title": "Ignatius CSB — In the beginning",
             "html": "..."
           }
         ]
       }
     }
   }
   ```
2. **UI Presentation (Preserving Russian Dolls + Parallel):**
   - Add a **Doll 1 Footnote Superscript Mode** (toggleable `Inline [tn/tc/sn]` badges beside English words or verse tail).
   - Add **Doll 5: Multi-Tradition Footnotes & Study Commentary** (filterable by Tradition/Source pill: `All`, `Catholic (Ignatius)`, `NET (tn / tc / sn)`, `Academic (NOAB / SBL)`, `Evangelical (NIV SB)`, `Jewish (JSB)`).
   - Add **By-Source Chapter & Book Introductions Drawer** (`book_intros.js` lazy shard) so Ignatius, NOAB, SBL, and JSB book introductions load on chapter demand.
   - Add `net21` and `bsb` cleanly to `TRANSLATION_REGISTRY` with accurate `[66b]` / `[STUDY]` badges (never falsely labeled `[IMPRIMATUR]`).

### Feature B — 3D/VR Tap-to-Float Node Popover + One-Click "Pin to Inspector"
Currently in `logos_suite_template.html`, `inspectWordFrom3D(wordObj)` updates `#morphInspectorContent` in the docked right pane, which is off-screen or below the fold when `#threeDViewport` is in `Expand ⤢` (`70vh`) or fullscreen/VR mode.
1. **Floating Anchored Popover (`#spatialWordCard` inside `#threeDViewport`):**
   - On 3D word click (`on3DPointerUp`, `movedDist <= 5`):
     - Highlight the word on the 3D `<canvas>` (`selected3DWord` — already implemented).
     - Project the word's 3D world coordinate (`localPt -> mesh.localToWorld(v) -> v.project(camera3D)`) to screen `(x, y)` inside `#threeDViewport`, clamping inside bounds so it never clips off-edge.
     - Render `#spatialWordCard` right beside the tapped 3D word showing: Lemma, Transliteration, Full Morphology (`decodeMorph`), Strong's Gloss + Derivation, In-Verse Witness Links, **`[📌 Pin to Inspector]`**, **`[Concordance]`**, and **`[✕]`**.
     - Call `updateSpatialCardPosition()` inside `animate3D()` whenever the camera orbits or planes drag so the card stays tethered like an AR/VR node until dismissed or pinned!
   - **Clicking `📌 Pin to Inspector`:** Calls `inspectWordFrom3D(wordObj)` + forces `#rightInspector` open (`hidden` removed) and docks/locks the active Inspector tab (`pinnedInspectorWord = true`), turning the floating node into a persistent docked study panel.

### Feature C — Improved Logos / Verbum Workspace Tabs + Link Sets
Replace fixed single center/right panels with a lightweight **Workspace Tab Manager** (`localStorage`-persisted `workspaceTabs`):
- **Multi-Tab Bar above Center Pane:** `[+] New Tab` opens independent reading tabs (`John 1:1 [DRA + NET Notes]`, `Gen 1:1 [WLC + LXX + Vulgate]`, `Amos 9:11 [LXX vs MT Crux]`, plus embedded Legacy Tools tab: `Omitted Verses` / `Patristic Timeline` / `Defeater Tree`).
- **Sync Groups (`Link Set A` / `Link Set B` / `Unlinked`):** Tabs sharing a Link Set navigate together synchronously when clicking cross-references or Concordance results; `Unlinked` tabs freeze on comparison verses (classic Verbum split-pane advantage, without desktop app bloat).
- **Layout Presets:** `Dolls Deep Dive`, `4-Column Textual Lab`, `Biblicum Language Drill` (Hides English or blurs Doll 1 until clicked to reveal!).

### Feature D — Curriculum-Tailored Scholar Profile & AI Study Tutor Bridge (`🎓 Scholar Mode`)
Grounded strictly in `C:\Users\Elation\Scholar_Decade_Plan\THE_SCHOLARS_ROADMAP_2026-10-14.md` & `CAREER_AND_EDUCATION_PATHWAYS_2026-10-14.md` `[V]`:
- **James's Actual Academic Track (Verified from Roadmap §1 & §4):**
  - Combines **Apologetics / Catholic-Protestant Debate (`G1`)**, **Textual Criticism & Second Temple / DSS / LXX (`G2`)**, and the **Dissertation (`G3`)**, with formal/self-study progression toward **Biblicum Gate A (~510 hrs parallel Biblical Hebrew & Koine Greek — Judges & Mark/John without dictionary)** → **Intermediate Greek/Hebrew (~300 hrs)** → **Biblical Aramaic (`~80 hrs`) & Ecclesiastical/Jerome Latin (`~300 hrs`)** → **Reading German/French** → **Patristics primary critical editions (`PL/PG/CCSL/SC`)** and **MA / PhD / SSL** readiness (note: **parallel Hebrew + Greek**, not dropping Greek).
- **UI Features to Implement in Right Inspector (`🎓 Scholar` Tab):**
  1. **Blind Translation Drill Mode:** Hides English Doll 1 / interlinear glosses on toggle so James translates straight from WLC Hebrew, Rahlfs LXX, Critical/Byzantine GNT, or Clementine Vulgate; click any word or hover only when stuck (mimicking Biblicum Gate A!).
  2. **Vocab Frequency Tier Tagging:** Badge Strong's words by NT/OT frequency (`<=50x`, `50–200x`, `200+x Core Biblicum Vocab`) so daily reading targets high-yield lexical acquisition.
  3. **Custom AI Tutor Context Exporter (`Copy Verse Dossier Prompt` + Optional Local Ollama/API Hook):** One click packages the active verse's 12+ witnesses, parsed morphology, Strong's glosses, NET `tn`/`tc` variants, Ignatius note, and James's **Scholar Track Profile** (parallel Hebrew/Greek/Latin + textual criticism + patristics) into a structured prompt or optional `localhost:11434` (Ollama) query — preserving 100% offline deterministic safety by default!

---

## 4. Verification Contract (Must Pass Before Shipping Any Edit)
Run both existing verification suites after every build of `build_plenary_logos_suite.py`:
1. `python "C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\web_app\build_plenary_logos_suite.py"` → must exit `0` cleanly.
2. `python "C:\Users\Elation\.gemini\antigravity\brain\4c9882d5-5ddc-4c53-99c2-9f34480554d1\scratch\verify_suite.py"` → verifies `0` external CDNs, `0` missing CSS classes in `tailwind_compiled.css`, `0` `CPDV` occurrences, 73-book completeness, Node VM morphology/concordance logic, and Chrome DOM load (`0` console errors). Extend it to assert `bsb`, `net21`, and JSONP shard schema integrity!
3. `node "C:\Users\Elation\.gemini\antigravity\brain\4c9882d5-5ddc-4c53-99c2-9f34480554d1\scratch\verify_3d_expand.mjs"` → verifies headless Chromium WebGL rendering (`Docked`, `Expanded 70vh`, `VR Arc`, `3D UV word click`, `Pin to Inspector`, fallback banners, zero black box), then visually inspect every regenerated PNG via `read_file`.

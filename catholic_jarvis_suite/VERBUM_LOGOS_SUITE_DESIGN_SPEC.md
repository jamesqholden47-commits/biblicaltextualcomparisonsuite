# 🏛️ VERBUM & LOGOS CATHOLIC STUDY SUITE — 1:1 FEATURE PARITY SPECIFICATION & ARCHITECTURAL BLUEPRINT

**Project:** *History Proves Catholicism* / CatholicJarvis Work Suite  
**Date:** 2026-10-09  
**Status:** In Active Implementation  

---

## 🎨 1. UI/UX INTERFACE MOCKUPS & VISUAL BENCHMARKS

The interface has been pre-rendered into three visual mockups establishing the layout, typography, palette, and information hierarchy for the suite:

### Mockup 1: Master 4-Pane Synchronized Workspace & Interlinear Ribbon
- Top Control Bar: Quick passage command bar (`Luke 1:1-4`), layout presets selector, tools/guides dropdown, and workspace modes.
- 4-Pane Docking Grid:
  - **Pane 1 (Top Left):** Greek New Testament (NA28 / MorphGNT) with majuscule/minuscule lines and Link Set A badge.
  - **Pane 2 (Top Right):** Latin Clementine Vulgate (*Vulgata Sixto-Clementina*) synchronized to Link Set A with soft gold active-verse selection.
  - **Pane 3 (Bottom Left):** Parallel English Translations (Douay-Rheims 1899 & RSV-2CE) synchronized to Link Set A.
  - **Pane 4 (Bottom Right):** Patristic Commentary & Catena Aurea (Aquinas, Chrysostom, Augustine, Jerome) auto-aligned to the active verse.
- Bottom Morphological Interlinear Ribbon: Expandable multi-tier ribbon displaying Surface Text, Lemma, Morphological Parsing, Strong's Number, and BDAG/Thayer Definition.

---

### Mockup 2: Catholic Exegetical Passage Guide & Dogmatic Factbook
- Left Navigation Panel (The Passage Guide):
  - Section 1: Parallel Passages (Synoptics & Harmony).
  - Section 2: Church Fathers & Catena Commentary (Homilies, Epistles, Aquinas).
  - Section 3: Magisterial Dogma (Catechism of the Catholic Church §§ & Denzinger Enchiridion DH numbers).
  - Section 4: Manuscript Witnesses (Direct integration with the 16 3D WebGL codices in CatholicJarvis: Codex Vaticanus, Sinaiticus, P75, P52, etc.).
  - Section 5: Cross References (Covenantal & Typological links).
  - Section 6: Grammatical & Textual Highlights.
- Center Column: Scripture text with inline commentary markers and highlight overlays.
- Right Column: Exegetical Detail Card showing lemma breakdown, syntactic analysis, and physical manuscript visual exhibits.

---

### Mockup 3: Side-by-Side Text Comparison Matrix & Difference Highlighting
- Multi-Translation Parallel Grid: Side-by-side columns comparing Greek NA28, Latin Clementina, Douay-Rheims, and RSV-2CE (plus KJV/Vulgate Nova).
- Visual Difference Engine: Soft red strikeouts indicating textual and translation divergences; soft gold/green highlights for matching pivotal Catholic doctrinal terms (e.g. *kecharitōmenē* = *gratia plena* = *full of grace*; *mysterion* = *sacramentum*; *dikaioō* = *iustificare*).
- Quick Passage Selector & Export: Instant switching between key debate battlegrounds with one-click export to Faithlife/Logos clippings.

---

## 🏗️ 2. ENGINEERING ROADMAP & COMPONENT BREAKDOWN

### Backend Core (`modules/verbum_logos_core.py`)
1. **Corpus Registry & Scripture Index:**
   - Multi-text database covering Greek (NA28/MorphGNT), Latin (Clementina/Nova), English (Douay-Rheims/RSV-2CE), Hebrew (WLC), and KJV.
   - Comprehensive Patristic Corpus: Aquinas Catena Aurea, Cornelius à Lapide, Haydock.
   - Magisterial & Dogmatic Cross-Index: CCC §§ and Denzinger DH anchors.
   - Manuscript Evidence: Deep links into CatholicJarvis 16 3D WebGL manuscripts.
2. **FastAPI Endpoints (`modules/verbum_logos_routes.py`):**
   - `GET /api/verbum/passage`: Multi-translation scripture.
   - `GET /api/verbum/interlinear`: Morphological parsing and BDAG breakdown.
   - `GET /api/verbum/guide`: Catholic Passage Guide.
   - `GET /api/verbum/compare`: Side-by-side text comparison with word diff.
   - `GET /api/verbum/search`: Full-text & lemma search.
   - `POST /api/verbum/export`: Export to Logos clippings.

### Frontend Module (`static/modules/verbum_logos.js`)
1. **Dockable Multi-Pane Layout Engine:** 1-pane, 2-pane, 3-pane, 4-pane grid with active focus and resource select.
2. **Synchronized Scrolling via Link Sets:** Link Set A, Link Set B, Unlinked.
3. **Morphological Interlinear Ribbon:** Interactive bottom ribbon and word inspector.
4. **Passage Guide & Exegetical Drawer:** Accordion panels for Church Fathers, Dogma, Manuscripts.
5. **Text Comparison Tool Tab:** Matrix with diff highlighting.
6. **Design Tokens:** 100% compliant with `jarvis.css`.

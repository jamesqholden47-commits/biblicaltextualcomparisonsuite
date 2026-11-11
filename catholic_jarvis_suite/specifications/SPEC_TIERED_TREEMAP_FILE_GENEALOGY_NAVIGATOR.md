# 🏛️ SPECIFICATION: TIERED TREE MAP & VISUAL GENEALOGY FILE NAVIGATOR
## Visual Ergonomics, Causal DAG Mechanics, and Interactive Spatial Stratigraphy for the CatholicJarvis Work Suite

**Document Version:** 1.0.0-PROPOSAL  
**Author:** Antigravity Architect & Senior UX Systems Engineer  
**Date:** 2026-10-10  
**Target Path:** `09_APPS_CATHOLICJARVIS/catholic_jarvis_suite/specifications/SPEC_TIERED_TREEMAP_FILE_GENEALOGY_NAVIGATOR.md`  
**Governing Laws Enforced:** Rule 1 (Theology Ungated), Rule 3 (Falsifiable Checks), Rule 4 (AI Provenance Isolation), Rule 5 (Ground-Truth Over Memory), Rule 6 (Move-Don't-Delete, L3 Full Byte-Hash), Rule 8 (Distill to Disk Before Chat), Rule 9 (HQSA Source-in-Folder), Rule 11 (Absolute Lossless Consolidation), Rule 12 (Citation Change Ledgering / Traceability), Rule 13 (Subject vs Infrastructure Segregation), Rule 14 (Code/Exhibit Quoted Span Stripping).

---

## 1. 🎯 EXECUTIVE SUMMARY & JAMES'S ARCHITECTURAL VISION

### 1.1 The User's Direct Prompt & Cognitive Dilemma
> *"A TIERED TREE MAP OF EVERY NOTE I'VE EVER WRITTEN WHETHER TXT OR MD; INCLUDING NOTES AND FILES YOUIVE MADE ME INCLUDING SCRIPTS AND FOLDERS; ALL TIERED WITH TGGLABLE SORTING BY DATE MODIFIED DATE ACCESSED DATE CREATED; AND THEN SEPERATE CATEGORIZATIION BY GENERAL CATEGORIE OR VICE VERSA IF YOU FIND BETTER SORTING METHODS IN COLOR CODING TOO MAYHAPS; THIS WAY I CAN SEE WHAT FILE CAUSED WHICH FILE AND SO ON AND SO ON I THINK THATS THE BEST WORK SUITE FILE NAVIGAATOR FEATURE I CAN THINK OF THAT ID ACTUALLY USE SINCE NONE OF THE CURRENT ONES LOOK INTUITIVE BUT KEEP THEM NONETHELESS; RUN SUBAGENTS TO UNDERSTAND WHAT IM TRYING TO PROMPT AND HELP ME FIND BETTERMENTS. like in this a color coding sorthign method could like color code BOOKS REPORTS DOSSIERS MONOGRAPHS ETC AND I COULD SEE FILES THAT STEM FROM BOOKS ETC;"*
> — **James, October 2026**

### 1.2 The Forensic Diagnostic: Why the Standard File Tree is Dead
For decades, computing has relied on the hierarchical collapsible file tree (`TreeView` / Explorer / Finder / VS Code Side Bar). In an academic and dialectical mega-project like *History Proves Catholicism* (spanning **28M tokens**, **513+ specialized research dossiers**, **thousands of primary source patristic/rabbinic PDFs**, and **hundreds of automation tools** across multi-vault stratigraphies `_PROJECT_HistoryProvesCatholicism`, `aa1`, `Mexico_Protestantism_Study`, and `PDFS`), the standard file tree fails catastrophically in four fundamental dimensions:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      THE 4 FATAL FAILURES OF STANDARD FILE TREES                       │
├──────────────────────────────┬─────────────────────────────────────────────────────────┤
│ 1. Metric Blindness          │ A 200-byte stub looks visually identical to an 800 KB    │
│    (Mass & Density Ignored)  │ 40-page patristic dossier or a 250 MB critical edition. │
├──────────────────────────────┼─────────────────────────────────────────────────────────┤
│ 2. Causal Amnesia            │ Folders tell you WHERE a file sits physically, never    │
│    (Lineage Severed)         │ WHY it was written, WHAT spawned it, or WHERE it went.  │
├──────────────────────────────┼─────────────────────────────────────────────────────────┤
│ 3. Temporal Compression      │ A file modified today is nested alongside a baseline    │
│    (Loss of Geological Time) │ file sealed 3 months ago with no visual temporal depth. │
├──────────────────────────────┼─────────────────────────────────────────────────────────┤
│ 4. Semantic Flattening       │ A Python automation verifier (infrastructure) looks the │
│    (Rule 13 Violation)       │ same as a Qumran 4QMMT analysis (theological subject).  │
└──────────────────────────────┴─────────────────────────────────────────────────────────┘
```

### 1.3 The Solution: The Tiered Tree Map & Visual Genealogy Navigator
The proposed subsystem within the **CatholicJarvis Work Suite** replaces passive folder browsing with an **active, bi-directional, spatio-temporal knowledge navigator**. It unifies:
1. **Spatial Mass Awareness:** A zoomable, squarified treemap and multi-tiered sunburst where node area reflects real substantive mass (bytes, line counts, or citation density).
2. **Epistemic Causality (The Genealogy DAG):** A directed acyclic graph visualizing the derivation lifecycle:
   $$\text{Primary Source [PDF]} \longrightarrow \text{Extraction Receipt [Fleet]} \longrightarrow \text{Research Dossier} \longrightarrow \text{Collation Draft} \longrightarrow \text{Master Dissertation / Volume}$$
3. **Ergonomic Dynamic Pivoting:** Instantaneous toggling between Folder-Centric, Category-Centric, Temporal-Centric, and Causal grouping hierarchies.
4. **Semiotics & High-Contrast Chromatic Encoding:** Strict adherence to `jarvis.css` dark-mode tokens with vibrant, functional categorization.
5. **Interactive Chrono-Scrubber:** A timeline slider allowing James to scrub across project history (July 2026 $\rightarrow$ October 2026), watching nodes spawn, expand, and synthesize across time.

---

## 2. 🌌 THE FOUR CORE VISUAL PARADIGMS

To satisfy James's desire for an intuitive navigator that he will *"actually use,"* the system implements four synchronized visual paradigms accessible via an ergonomic top-level view switcher (`Ctrl+1` through `Ctrl+4`):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE 4 VIEW MODES IN CAROUSEL                              │
├──────────────────────────────┬──────────────────────────────┬──────────────────────────┤
│ VIEW 1: SQUARIFIED TREEMAP   │ VIEW 2: MULTI-TIER SUNBURST  │ VIEW 3: GENEALOGY DAG    │
│ • Spatial mass distribution  │ • Concentric radial rings    │ • Directed causality flow│
│ • Zoomable nested rectangles │ • Center = Master core       │ • Upstream & downstream  │
│ • Node area = Lines / Bytes  │ • Angle = Relative volume    │ • Parents -> Descendants │
├──────────────────────────────┴──────────────────────────────┴──────────────────────────┤
│ VIEW 4: HYBRID BI-DIRECTIONAL DECK (SYNCHRONIZED SPLIT-VIEW)                           │
│ • Left Viewport: Spatial Treemap / Sunburst (Mass, Category, Cluster)                 │
│ • Right Viewport: Causality DAG (Lineage, Inception, Master Absorption)               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.1 Paradigm 1: Squarified Nested Treemap (D3/Canvas Space-Filling)

The Treemap translates the entire disk repository into a two-dimensional mosaic of rectangles, nested hierarchically.

```
+---------------------------------------------------------------------------------------+
|  01_MASTER_DISSERTATION (Imperial Purple / Royal Gold)                                 |
|  +-----------------------------------+ +--------------------------------------------+ |
|  | MASTER_DISSERTATION_PROTESTANT... | | DISSERTATION_OCTOBER_CONSOLIDATED...       | |
|  | 285 KB | 3,420 Lines | [V: 161]   | | 412 KB | 5,110 Lines                       | |
|  +-----------------------------------+ +--------------------------------------------+ |
+---------------------------------------------------------------------------------------+
|  03_RESEARCH_DOSSIERS (Cobalt Blue / Azure)                                           |
|  +------------------------+ +------------------------+ +----------------------------+ |
|  | 4QMMT_Works_Law.md     | | Forensic_Justif.md     | | Boyarin_Border_Lines.md    | |
|  | 145 KB | 1,820 Lines   | | 210 KB | 2,450 Lines   | | 98 KB | 1,120 Lines        | |
|  +------------------------+ +------------------------+ +----------------------------+ |
+---------------------------------------------------------------------------------------+
|  PDFS / PRIMARY SOURCES   | FLEET REPORTS & RECEIPTS | SCRIPTS & VERIFIERS (Teal)   |
|  (Deep Crimson / Gold)    | (Emerald Green)          | +--------------------------+ |
|  +----------------------+ | +----------------------+ | | drift_check.py | 34 KB   | |
|  | Migne_PG_Vol48.pdf   | | Subagent_65_Extract.md | +--------------------------+ |
|  | 18.4 MB (Scaled)     | | 85 KB | 1,100 Lines    | | loss_check.py  | 10 KB   | |
|  +----------------------+ +------------------------+ +--------------------------+ |
+---------------------------------------------------------------------------------------+
```

#### Mathematical Layout & Ergonomics
- **Algorithm:** Bruls-Huizing-van Wijk squarified treemap layout algorithm. Rectangles maintain an aspect ratio as close to $1.0$ (golden ratio / square) as possible, preventing thin, unreadable slivers.
- **Node Size Metrics (Togglable):**
  1. *Substantive Line Count:* Ignores binary mass; highlights intellectual prose density.
  2. *Byte Size (Logarithmic Scaling for PDFs):* Uses $\log_2(\text{bytes})$ compression for large PDFs so an 80 MB scanned codex does not swallow the entire screen, while still visually demonstrating heavy gravitas over a 2 KB stub.
  3. *Citation / Footnote Density:* Node area proportional to patristic and scripture citations count (`[^N]` + `(PG ...)` + `DH ...`).
- **Semantic Zooming:**
  - *Level 0 (Global Vault Panorama):* High-level categorical containers (`MASTER`, `DOSSIERS`, `BOOKS`, `STATE`, `SCRIPTS`).
  - *Level 1 (Folder / Campaign Cluster):* Double-clicking zooms smoothly into a campaign (e.g., `03_RESEARCH_DOSSIERS/_BINDINGNESS_FLEET/`).
  - *Level 2 (Individual File Card):* Displays title, line count, status badges, verification tier, and preview excerpt.
  - *Level 3 (Intra-File Structural Anchors):* For files $>50\text{ KB}$, the card subdivides into internal H1/H2 chapters, insertion blocks, and footnote apparatus sections.
- **Breadcrumb Navigation Strip:** Fixed header breadcrumb: `Root / 03_RESEARCH_DOSSIERS / _JUSTIFICATION / Forensic_Justification_Subagent_Raw_Extract.md` with instant one-click step-back.

---

### 2.2 Paradigm 2: Sunburst Multi-Tiered Radial Partition

The Sunburst partition visualizes the corpus as an epistemic astrolabe or concentric monastic wheel. It is particularly intuitive for grasping hierarchical depth from the project core out to granular evidentiary citations.

```
                          . - ~ ~ ~ - .
                      . '  [RING 3: FILES] ' .
                  . '  [RING 2: CATEGORIES]    ' .
                /       [RING 1: MAJOR VAULTS]     \
               /     /-------------------------\     \
              |     |       RING 0: CORE        |     |
              |     |  *History Proves Cath.*   |     |
              |     |   28M Tokens | 161 [V]    |     |
               \     \-------------------------/     /
                \       [RING 1: MAJOR VAULTS]     /
                  . .  [RING 2: CATEGORIES]    . .
                      ' .  [RING 3: FILES] . '
                          ' - ~ ~ ~ - '
```

#### Concentric Geometry & Radial Stratigraphy:
- **Ring 0 (Center Hub - 15% Radius):** The Master Project Sun. Displays global health: Total Word Count, Rule 11 Parity Status (`PASS`), Active Anchor Cursor (`DRIFTCHECK-PASS`), and Active Working Volume. Clicking resets zoom to root.
- **Ring 1 (Major Vault Divisions - 25% Radius):**
  - Quadrant I: `01_MASTER_DISSERTATION` & `10_VOLUMES` (Monographs)
  - Quadrant II: `03_RESEARCH_DOSSIERS` (Subject Intelligence)
  - Quadrant III: `PDFS` & `06_SOURCE_MATERIAL` (Primary Witnesses)
  - Quadrant IV: `02_CONTROL_AND_STATE` & `09_APPS_CATHOLICJARVIS` (Infrastructure & Apps)
- **Ring 2 (Content Sub-Categories - 45% Radius):** Campaign clusters, e.g., `_EUCHARISTIC_FLEET`, `_JUSTIFICATION_FLEET`, `_PAPAL_PRIMACY`, `PATRISTIC_GREEK_CORPUS`.
- **Ring 3 (Individual Files - 75% Radius):** Every `.md`, `.txt`, `.py`, `.pdf` represented as a discrete arc slice. Arc angle $\theta$ is proportional to the selected sort metric (Lines / Size).
- **Ring 4 (Outer Corona / Micro-Anchors - 100% Radius):** Footnotes `[^1]` through `[^161]`, insertion chunks, and Patristic Latin/Greek lemmas.
- **Interactive Arc Physics:**
  - Hovering an arc expands its radial thickness by $15\%$, dims all unrelated arcs, and displays a tooltip HUD showing path, size, date, and causal parent.
  - Clicking an arc triggers an animated radial zoom (D3 `arcTween`), smoothly rotating and enlarging that partition into the new full circle.

---

### 2.3 Paradigm 3: The Genealogy & Causality DAG (Directed Acyclic Graph)

This is the central innovation requested by James:
> *"THIS WAY I CAN SEE WHAT FILE CAUSED WHICH FILE AND SO ON AND SO ON... AND I COULD SEE FILES THAT STEM FROM BOOKS ETC"*

Standard file browsers are static storage views. The **Genealogy DAG** transforms files into a **causal derivation pipeline**.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             THE 5-STAGE CAUSAL DERIVATION PIPELINE                               │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

 [STAGE 0: PRIMARY SOURCE]         [STAGE 1: AI FLEET EXTRACT]        [STAGE 2: SYNTHESIZED DOSSIER]
 ┌────────────────────────┐        ┌─────────────────────────┐        ┌────────────────────────────┐
 │ PDFS/                  │───────>│ 06_SOURCE_MATERIAL/     │───────>│ 03_RESEARCH_DOSSIERS/      │
 │ Sanders_Paul_1977.pdf  │        │ Sanders_Extract_65A.md  │        │ Forensic_Justification.md  │
 │ [BOOK: 420 pp]         │        │ [RECEIPT: 12 subagents] │        │ [DOSSIER: 18,400 words]    │
 └────────────────────────┘        └─────────────────────────┘        └────────────────────────────┘
             │                                                                      │
             │ (Cites Greek NA28)                                                   │ (Lossless Merge)
             ▼                                                                      ▼
 ┌────────────────────────┐                                           ┌────────────────────────────┐
 │ 06_SOURCE_MATERIAL/    │                                           │ 01_MASTER_DISSERTATION/    │
 │ Rom3_28_MorphGNT.json  │──────────────────────────────────────────>│ MASTER_DISSERTATION_v2.md  │
 └────────────────────────┘                                           │ [MASTER: Ch. 4 §2 - ^77]   │
                                                                      └────────────────────────────┘
                                                                                    │
                                                                                    │ (Audio Synthesis)
                                                                                    ▼
                                                                      ┌────────────────────────────┐
                                                                      │ 09_APPS_CATHOLICJARVIS/    │
                                                                      │ Episode_04_Justif_DR.mp3   │
                                                                      │ [STUDIO PODCAST]           │
                                                                      └────────────────────────────┘
```

#### Graph Construction Engine (`modules/genealogy_core.py`):
1. **Node Properties:**
   - Every file is a graph node $N_i$ with metadata $\{ \text{id}, \text{path}, \text{category}, \text{mtime}, \text{ctime}, \text{size}, \text{lines}, \text{tier}, \text{hash} \}$.
2. **Directed Edge Semantics ($E_{ij} = N_i \xrightarrow{\text{rel}} N_j$):**
   - `STEMS_FROM` / `EXTRACTED_FROM`: Node $N_j$ (Dossier) was generated by analyzing Node $N_i$ (Book/PDF).
   - `ABSORBED_INTO`: Node $N_i$ (Dossier) was losslessly consolidated into Node $N_j$ (Master Monograph) under Rule 11.
   - `CITES`: Node $N_j$ contains a formal markdown footnote reference `[^N]` or bibliographical citation pointing to $N_i$.
   - `AUTOMATED_BY`: Node $N_j$ (State/Manifest) is audited or generated by Node $N_i$ (Script).
   - `PROMPTED_BY`: Node $N_j$ (Research Output) was spawned by Node $N_i$ (Session Log / Prompt Transcript).
3. **Automated Causality Detection Mechanisms:**
   - *Direct Footnote Scanning:* Scans all markdown for path/name mentions, `PDFS/...` links, and exact title matches.
   - *Rule 12 Session Log Ingestion:* Parses `_AG_SESSION_LOG_*.md` and `_SESSION_TRANSCRIPTS/*.md` which explicitly record: `"Agent extracted Sanders.pdf -> created Forensic_Justification_Subagent_Raw_Extract.md"`.
   - *Git Inception Correlation:* Reads repository commit histories. When Commit $C_A$ adds File $A$, and Commit $C_B$ ($T_B > T_A$) adds File $B$ containing $>40\%$ line overlap or explicit citation of $A$, a causal directed edge is forged.
   - *Rule 14 Quoted-Span Stripping:* During parsing, all code spans and audit table exhibits are stripped so that files documenting defects (e.g., `05_VERIFICATION_OF_FLEET_CLAIMS.md`) are not falsely inferred as parent sources.

---

### 2.4 Paradigm 4: Hybrid Bi-Directional Synchronized View

The Hybrid View is the power-user workhorse. It features a split-screen deck that marries **Spatial Mass** with **Causal Derivation**:

```
+--------------------------------------------------------------------------------------------------+
| CATHOLICJARVIS FILE NAVIGATOR — HYBRID DECK                            [View: Treemap + DAG | v] |
+---------------------------------------------------+----------------------------------------------+
| LEFT PANE: SPATIAL TREEMAP (Mass & Density)       | RIGHT PANE: CAUSALITY FLOW (Derivation Line) |
|                                                   |                                              |
| +--------------------+ +-------------------------+| [Sanders_1977.pdf] (Primary Book)            |
| | 01_MASTER_...      | | 03_RESEARCH_DOSSIERS    ||         |                                    |
| |                    | | +---------------------+ ||         v                                    |
| |                    | | | Forensic_Justif.md  | || [Sanders_Extract_65A.md] (Receipt)           |
| |                    | | | >>> SELECTED <<<    | ||         |                                    |
| |                    | | +---------------------+ ||         v                                    |
| +--------------------+ +-------------------------+| [Forensic_Justif.md]  <<< FOCUSED NODE       |
|                                                   |         |                                    |
| +--------------------+ +-------------------------+|         v                                    |
| | PDFS/ (Books)      | | 02_CONTROL_AND_STATE    || [MASTER_DISSERTATION_v2.md] (Ch. 4)          |
| +--------------------+ +-------------------------+|         |                                    |
+---------------------------------------------------+----------------------------------------------+
| FOOTER TELEMETRY & CHRONO-SCRUBBER: [<<<] [ |> PLAY ] [>>>]  | July 2026 ======O====== Oct 2026   |
+--------------------------------------------------------------------------------------------------+
```

#### Bi-Directional State Synchronization (`window.GenealogyBridge`):
- Selecting a node in the Treemap highlights its exact derivation path in the DAG.
- Selecting a node in the DAG zooms the Treemap to focus on its physical cluster.
- Splitting ratio is freely draggable via an ergonomic split gutter (`min: 20%`, `max: 80%`).

---

## 3. 🎛️ ADVANCED ERGONOMIC TOGGLABLE SORTING & GROUPING CONTROLS

James emphasized:
> *"ALL TIERED WITH TGGLABLE SORTING BY DATE MODIFIED DATE ACCESSED DATE CREATED; AND THEN SEPERATE CATEGORIZATIION BY GENERAL CATEGORIE OR VICE VERSA IF YOU FIND BETTER SORTING METHODS IN COLOR CODING TOO MAYHAPS"*

To provide frictionless ergonomics, the navigator exposes a unified **Omni-Control Toolbar** at the top of the interface:

```
[ GROUP BY: (•) Category  ( ) Folder  ( ) Timeline  ( ) Causal ] 
[ SORT BY:  [ Date Modified (mtime) |v] ] [ DIRECTION: [ Descending |v] ]
[ METRIC:   [ Substantive Lines     |v] ] [ FILTER: [ All Types (Subject Only) |v] ]
[ SEARCH:   [ filter by regex or filename...                              ] [Clear] ]
```

---

### 3.1 Primary Sort Dimensions

| Sort Dimension | System Attribute | Intellectual Meaning for James |
|---|---|---|
| **Date Modified (`mtime`)** | `os.stat().st_mtime` | **Recency of Active Craft:** Surfaces what is being written *right now*, revealing the hot cutting edge of the dissertation. |
| **Date Created (`ctime`/`btime`)** | `os.stat().st_ctime` | **Historical Inception:** Orders files by when the idea or document was first born into the ecosystem. |
| **Date Accessed (`atime`)** | `os.stat().st_atime` | **Research Focus:** Surfaces what source books, notes, or dossiers James has actively read or opened recently in CatholicJarvis or VS Code. |
| **Substantive Line Count** | Count of non-blank lines | **Intellectual Weight:** Filters out blank spacing and distinguishes massive, encyclopedic dossiers from short stubs. |
| **File Byte Size** | `os.stat().st_size` | **Storage Mass:** Formatted cleanly (`B`, `KB`, `MB`). Useful for tracking multi-megabyte PDF critical editions. |
| **Academic Tier (L1 / L2 / L3)** | Rule 6/9 Metadata Index | **Evidence Hardness:** L1 (Metadata/Citation only), L2 (Sampled text hash), L3 (Full byte-hash sealed + source in `PDFS`). |
| **Chronological Session Sequence** | Git commit index / Session log ID | **Campaign Iteration:** Groups files strictly by the work session in which they were generated (Session 1 $\rightarrow$ Session 120). |

---

### 3.2 Quad-Mode Grouping Hierarchy Toggle

The nesting structure of the Treemap, Sunburst, and DAG transforms instantly when toggling the grouping mode:

#### Mode A: Folder-Centric Hierarchy (Physical Filesystem Topology)
$$
\text{Root} \longrightarrow \text{Directory} \longrightarrow \text{Subdirectory} \longrightarrow \text{File}
$$
*Use case:* Traditional filesystem hygiene, verifying where files physically live on drive `C:`, spotting directory sprawl.

#### Mode B: Type-Centric Hierarchy (Ontological Functional Taxonomy)
$$
\text{Category (Books} \rightarrow \text{Dossiers} \rightarrow \text{Reports} \rightarrow \text{Monographs} \rightarrow \text{Scripts} \rightarrow \text{State)} \longrightarrow \text{Sub-Domain} \longrightarrow \text{Files}
$$
*Use case:* Pure academic research. Groups all books together regardless of whether they sit in `C:\Users\Elation\PDFS` or `06_SOURCE_MATERIAL`. Groups all dossiers together across `DXM` and `_PROJECT_HistoryProvesCatholicism`.

#### Mode C: Temporal-Centric Hierarchy (Geological Stratigraphy)
$$
\text{Year (2026)} \longrightarrow \text{Month (July / Aug / Sept / Oct)} \longrightarrow \text{Sprint Week} \longrightarrow \text{Daily Session Sprints} \longrightarrow \text{Artifacts}
$$
*Use case:* Retrospective review. Answering: *"What did I write in mid-August during the Justification sprint versus early October during the Verbum/Logos sprint?"*

#### Mode D: Genealogical / Causal Hierarchy (Derivation Lineage)
$$
\text{Primary Witness (Book)} \longrightarrow \text{Subagent Extraction Receipt} \longrightarrow \text{Synthesized Dossier} \longrightarrow \text{Collation Draft} \longrightarrow \text{Master Chapter}
$$
*Use case:* Direct traceability. Tracing prooftexts from their patristic origins straight into final dissertation footnotes.

---

## 4. 🎨 THE COLOR CODING & VISUAL SEMIOTICS SYSTEM

James specified:
> *"a color coding sorthign method could like color code BOOKS REPORTS DOSSIERS MONOGRAPHS ETC AND I COULD SEE FILES THAT STEM FROM BOOKS ETC"*

To achieve maximum visual clarity without eye fatigue, the color system is built strictly from the tokens established in `jarvis.css`. Every category features an unambiguous primary hue, background card tint, accent border, and unmistakable semantic badge:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        THE 7-CATEGORY MASTER CHROMATIC PALETTE (JARVIS-COMPLIANT)                  │
├─────────────────────┬──────────────┬──────────────┬──────────────┬───────┬─────────────────────────┤
│ CATEGORY            │ PRIMARY HUE  │ BG SURFACE   │ ACCENT BORDER│ BADGE │ RECIPIENT ENTITIES      │
├─────────────────────┼──────────────┼──────────────┼──────────────┼───────┼─────────────────────────┤
│ 1. BOOKS & SOURCES  │ Deep Crimson │ #2a1115      │ #ef4444      │ 📜 B  │ PDFS, Migne PG/PL,      │
│                     │ (#ef4444)    │ (Ruby Dusk)  │ Gold border  │       │ Septuagint, DSS, Vulgate│
├─────────────────────┼──────────────┼──────────────┼──────────────┼───────┼─────────────────────────┤
│ 2. RESEARCH DOSSIER │ Cobalt Azure │ #0f1d36      │ #38bdf8      │ 🔬 D  │ 03_RESEARCH_DOSSIERS,   │
│                     │ (#38bdf8)    │ (Cobalt Deep)│              │       │ Patristic deep studies  │
├─────────────────────┼──────────────┼──────────────┼──────────────┼───────┼─────────────────────────┤
│ 3. FLEET RECEIPTS   │ Emerald Green│ #062b1e      │ #10b981      │ ⚡ R  │ Subagent reports, OCR   │
│                     │ (#10b981)    │ (Mint Shadow)│              │       │ extractions, raw tools  │
├─────────────────────┼──────────────┼──────────────┼──────────────┼───────┼─────────────────────────┤
│ 4. MASTER MONOGRAPH │ Imperial     │ #261338      │ #a78bfa      │ 👑 M  │ 01_MASTER_DISSERTATION, │
│    & DISSERTATION   │ Purple/Gold  │ (Byzantine)  │ #d4af37      │       │ 10_VOLUMES, Opus        │
├─────────────────────┼──────────────┼──────────────┼──────────────┼───────┼─────────────────────────┤
│ 5. STATE & CONTROL  │ Amber Flame  │ #2e1c08      │ #f59e0b      │ 🛡️ S  │ _BOOT_HEADER, CLAUDE.md,│
│                     │ (#f59e0b)    │ (Amber Night)│              │       │ _LIVE_CHECKPOINT, state │
├─────────────────────┼──────────────┼──────────────┼──────────────┼───────┼─────────────────────────┤
│ 6. AUTOMATION TOOLS │ Vivid Teal   │ #09262e      │ #06b6d4      │ ⚙️ A  │ .py scripts, verifiers, │
│                     │ (#06b6d4)    │ (Teal Depths)│              │       │ bridges, test suites    │
├─────────────────────┼──────────────┼──────────────┼──────────────┼───────┼─────────────────────────┤
│ 7. CONVERSATION LOG │ Muted Slate  │ #171b26      │ #64748b      │ 💬 L  │ Transcripts, prompts,   │
│    & PROVENANCE     │ (#64748b)    │ (Slate Grey) │              │       │ scratchpads, aa1 notes  │
└─────────────────────┴──────────────┴──────────────┴──────────────┴───────┴─────────────────────────┘
```

---

### 4.1 Visual Semiotics of State, Integrity, and Rule Compliance

Beyond category color, nodes display micro-badges and luminous borders encoding their academic and methodological status:

```
+------------------------------------------------------------------------+
|                      NODE SURFACE SEMIOTIC GLYPHS                      |
+------------------------------------------------------------------------+
|  [V] Emerald Tag     = Fully verified against named primary source     |
|  [R] Cyan Tag        = Reliably reported, secondary patristic source   |
|  [S] Amber Tag       = Stated / inferential hypothesis (needs verify)  |
|  (∞) Gold Infinity   = Losslessly Consolidated under Rule 11           |
|  [L3] Gold Shield    = Proof-Tier 3 (Full byte-hash sealed + in-folder)|
|  * Glow Pulse *      = Modified within the last 24 hours               |
|  -- Dashed Border -- = Infrastructure file (Rule 13 Firewall Active)   |
|  == Double Border == = Subject Master Dissertation Candidate           |
+------------------------------------------------------------------------+
```

---

## 5. ⚡ INTERACTIVE "BETTERMENTS" & MICRO-INTERACTIONS

To elevate the tool beyond static charts, four signature interactive mechanisms are integrated:

### 5.1 Betterment A: Click-to-Trace Lineage (Ancestral Illumination)

When James clicks on any file (e.g., `Forensic_Justification_Subagent_Raw_Extract.md`):
1. **Background Dimming:** All unrelated nodes in the Treemap, Sunburst, and DAG drop to $12\%$ opacity (`filter: blur(1px)`).
2. **Upstream Illumination (The Ancestral Bloodline):**
   - A golden luminescent curve (`stroke: #d4af37`, pulsing `animation: dash 1.5s linear infinite`) traces backward to every primary PDF, Scripture text, and session transcript that fed into this file.
3. **Downstream Illumination (The Descendant Arteries):**
   - An electric cyan curve (`stroke: #38bdf8`) shoots forward to every dissertation volume, insertion block, or audio podcast chapter that absorbed or cited this file.
4. **Ancestral HUD Breadcrumb:** An overlay pill displays:
   `Sanders_1977.pdf` $\xrightarrow{\text{extract}}$ `Extract_65A.md` $\xrightarrow{\text{synthesized}}$ **[Active Dossier]** $\xrightarrow{\text{absorbed}}$ `Master_Dissertation_v2.md`

```
 [Sanders_1977.pdf] ══(Gold Umbilical)══> [Forensic_Justif.md] ══(Cyan Artery)══> [Master_Ch4.md]
 (Upstream Origin)                           (ACTIVE NODE)                          (Final Destination)
```

---

### 5.2 Betterment B: The 2026 Chrono-Scrubber (Temporal Time Machine)

At the bottom of the navigator sits an interactive **Timeline Scrubber**:

```
[ |< ] [ << 5x ] [ > PLAY ] [ >> 5x ] [ >| LIVE ]  July 1, 2026 ────────●──────── Oct 10, 2026
```

#### Scrubber Mechanics:
- **Scrubbing Range:** July 2026 (Project Genesis & Methodological Charter) to October 2026 (Live Session Date).
- **Interactive Playback:** Pressing `Space` or clicking `Play` runs an automated playback of project development at $1\times$, $5\times$, or $25\times$ speed.
- **Node Birth Animations:** As the timeline progresses past a file's `ctime`, the node spawns on the screen with an organic scale-in bounce (`transform: scale(0) -> scale(1.05) -> scale(1.0)`).
- **Node Growth Physics:** As subsequent sessions append words and research into a file, the rectangle expands smoothly, allowing James to watch `01_MASTER_DISSERTATION` gradually consume research mass over time!
- **Milestone Bookmarks:** Key project milestones are marked with diamond pins along the track:
  - `◆ July 26:` Hook Teardown & Ext4 Superblock model
  - `◆ Aug 01:` Lossless Rule 11 & Citation Ledgering Rule 12 enacted
  - `◆ Sept 04:` Cannabis Bioethics & Patristic Synthesis
  - `◆ Oct 07:` CatholicJarvis Suite Phase 0/1 Overhaul
  - `◆ Oct 09:` Verbum/Logos 1:1 Parity Suite launch

---

### 5.3 Betterment C: Detail / Quick-Action Inspector Blade

Clicking any node immediately slides out the right-hand **Inspector Blade** (utilizing the responsive `#j-peek` panel styled in `jarvis.css`):

```
+-------------------------------------------------------------------------+
| INSPECTOR BLADE: Forensic_Justification.md                         [ X ]|
+-------------------------------------------------------------------------+
| [🔬 DOSSIER]  [V: Verified (18)]  [∞ Rule 11 Consolidated]  [L3 Byte-OK]|
+-------------------------------------------------------------------------+
| 📁 Path: 03_RESEARCH_DOSSIERS/_JUSTIFICATION/Forensic_Justif.md         |
| 📏 Metrics: 18,420 words | 2,450 lines | 145.2 KB                       |
| 🔒 SHA256: 3f8a91b2e6... | mtime: 2026-09-04 14:22:01                   |
| 📜 Patristic Citations: 42 (Chrysostom x14, Augustine x19, Aquinas x9)  |
| 🏛️ Scripture Loci: Rom 3:28, Rom 4:5, James 2:24, 4QMMT C26-32         |
+-------------------------------------------------------------------------+
| 🧬 ANCESTRY & GENEALOGY:                                                |
|   ▲ Upstream (Born from):                                               |
|     • Sanders_Paul_and_Palestinian_Judaism_1977.pdf [PDF: 540 pp]       |
|     • 06_SOURCE_MATERIAL/Subagent_65_Raw_Extract.md [Receipt]           |
|   ▼ Downstream (Absorbed into):                                         |
|     • 01_MASTER_DISSERTATION/MASTER_DISSERTATION_v2.md (Ch. 4, pp. 88) |
|     • 10_VOLUMES/VOL_02_JUSTIFICATION_AND_GRACE.md                      |
+-------------------------------------------------------------------------+
| ⚡ INSTANT ACTIONS:                                                     |
|   [ 📖 Open in Reader ]  [ 💻 Launch in VS Code ]  [ 📋 Copy Cite Tag ] |
|   [ 🔍 Run loss_check ]  [ 🛡️ Verify Rule 11 ]     [ 🎧 Generate Audio]|
+-------------------------------------------------------------------------+
```

---

### 5.4 Betterment D: Faceted Filter & Search HUD

Pressing `Ctrl+F` or `/` opens the in-canvas search HUD supporting structured queries:

- `cat:dossier`: Filters solely to research dossiers.
- `after:2026-09-01`: Displays files modified after September 1, 2026.
- `has:greek` or `has:hebrew`: Highlights documents containing original ancient language lemmas.
- `rule:subject`: Enforces Rule 13, hiding all infrastructure scripts, tools, and transcripts to show pure dissertation content.
- `is:orphan`: Identifies files with **zero** outgoing or incoming causal edges (unabsorbed notes or uncited sources requiring consolidation).

---

## 6. 🏗️ SYSTEM ARCHITECTURE & IMPLEMENTATION BLUEPRINT

The subsystem integrates cleanly into CatholicJarvis Suite (`09_APPS_CATHOLICJARVIS/catholic_jarvis_suite/`) following the established design pattern (`*_core.py`, `*_routes.py`, `static/modules/*.js`).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               COMPONENT ARCHITECTURE                                   │
└────────────────────────────────────────────────────────────────────────────────────────┘

  [ FRONTEND MODULE ]
  static/modules/genealogy_treemap.js
      │
      ├── Rendering Engine: D3.js v7 (Zoomable Squarified Treemap + Radial Sunburst)
      ├── Graph Layout Engine: Dagre.js (Layered Sugiyama DAG Layout)
      ├── State Store: window.GenealogyState (Active filters, zoom, selection)
      └── Styles: jarvis.css (.genealogy-*, --accent-*, --bg-*)
      │
      ▼ HTTP Fetch (JSON)
  [ FASTAPI ROUTES ]
  modules/genealogy_routes.py
      │
      ├── GET  /api/genealogy/tree     -> Hierarchical tree for Treemap/Sunburst
      ├── GET  /api/genealogy/graph    -> Node-link graph for DAG
      ├── GET  /api/genealogy/lineage  -> Upstream/Downstream paths for single node
      ├── GET  /api/genealogy/timeline -> Temporal chronological event log
      └── POST /api/genealogy/refresh  -> Trigger incremental re-index
      │
      ▼ Python Core Calls
  [ BACKEND CORE ENGINE ]
  modules/genealogy_core.py
      │
      ├── Filesystem Scanner: os.scandir with SHA-256 caching
      ├── Link & Citation Parser: Footnote regex, wikilink extractor, PDF scanner
      ├── Causality Inferrer: Git commit correlation, session log parser
      └── SQLite State Database: data/genealogy_cache.db
```

---

### 6.1 Backend Core Engine (`modules/genealogy_core.py`)

#### Data Models (JSON Schemas)

```python
# Node Data Schema
{
    "id": "rel_path_hash",
    "name": "Forensic_Justification.md",
    "path": "03_RESEARCH_DOSSIERS/_JUSTIFICATION/Forensic_Justification.md",
    "abs_path": "C:\\Users\\Elation\\DXM\\Clippings\\...\\Forensic_Justification.md",
    "category": "DOSSIER",          # BOOK, DOSSIER, FLEET, MASTER, STATE, SCRIPT, LOG
    "mtime": 1725459721.0,           # float timestamp
    "ctime": 1722510200.0,
    "atime": 1728570000.0,
    "size": 148684,                  # bytes
    "lines": 2450,                   # non-empty lines
    "words": 18420,
    "sha256_prefix": "3f8a91b2e6a4",
    "tier": "L3",                    # L1, L2, L3
    "verification": "V",             # V, R, S
    "has_greek": True,
    "has_hebrew": True,
    "is_infrastructure": False,      # Rule 13 flag
    "citations_count": 42
}

# Edge Data Schema
{
    "source": "parent_node_id",
    "target": "child_node_id",
    "type": "STEMS_FROM",            # STEMS_FROM, ABSORBED_INTO, CITES, AUTOMATED_BY
    "evidence": "Cited in footnote [^77] and logged in _AG_SESSION_LOG_2026-09-04.md",
    "confidence": 1.0                # 1.0 = explicit markdown link / git record; 0.8 = heuristic
}
```

#### High-Performance Indexing Strategy
- **Incremental Scanning:** Uses `os.scandir` with `st_mtime` checks against `data/genealogy_cache.db`. A cold scan of 10,000 files takes $\approx 1.8\text{ seconds}$; warm incremental scans complete in $<80\text{ ms}$.
- **Background Worker:** Runs on an asynchronous background thread, automatically updating when files are saved.
- **Rule 13 Filter Integration:** Directly reads `02_CONTROL_AND_STATE/_NOT_DISSERTATION_CONTENT.json` to guarantee automated segregation between infrastructure scripts and academic theological dossiers.

---

### 6.2 Frontend Module (`static/modules/genealogy_treemap.js`)

```javascript
/* genealogy_treemap.js — CatholicJarvis Tiered Treemap & Visual Genealogy Navigator
   Adheres 100% to jarvis.css tokens and shell architecture. */
(function () {
  "use strict";
  window.JarvisModules = window.JarvisModules || {};

  var State = {
    viewMode: "treemap",       // "treemap" | "sunburst" | "dag" | "hybrid"
    groupBy: "category",       // "category" | "folder" | "timeline" | "causal"
    sortBy: "mtime",           // "mtime" | "ctime" | "atime" | "lines" | "size"
    metric: "lines",           // "lines" | "size" | "citations"
    selectedNode: null,
    timeScrubberDate: null,
    searchQuery: "",
    subjectOnly: true          // Rule 13 filter toggle
  };

  function init(container) {
    container.className = "genealogy-root fx-root";
    renderToolbar(container);
    renderViewport(container);
    loadData();
  }

  // View rendering, D3 treemap / sunburst bindings, and Dagre graph layouts...
  window.JarvisModules.genealogy = { init: init, getState: function () { return State; } };
})();
```

---

## 7. 🛡️ VERIFICATION, FALSIFICATION & SAFETY INTEGRATION

In strict compliance with project laws, this specification mandates rigorous automated verification before any production deployment:

### 7.1 Compliance with Rule 3: Checks That Can Fail
1. **Node Count Parity Check:** The total node count reported by `GET /api/genealogy/tree` must match the exact file count on disk across configured roots. If a single `.md` file is missing, the endpoint emits `HTTP 500 [FAIL B1-COUNT]`.
2. **DAG Cycle Detector:** A Directed Acyclic Graph cannot contain cyclic loops ($A \rightarrow B \rightarrow C \rightarrow A$). An automated Tarjan / topological sort unit test runs on every graph build. Any detected cycle fails loudly.

### 7.2 Compliance with Rule 11: Absolute Lossless Consolidation
When James merges two files, the genealogy engine verifies that the downstream node links back to **both** parents. The `loss_check.py` tool is integrated into the node inspector; James can click `Verify Lossless Status` to assert that zero substantive sentences were dropped during consolidation.

### 7.3 Compliance with Rule 13: Subject vs Infrastructure Isolation
The UI provides an immutable **Subject/Infrastructure Divider Toggle**. When `Subject Only` is toggled:
- All `.py`, `.bat`, `.vbs`, and audit transcripts are excluded from the main dissertation hierarchy.
- The system prevents any user action that would accidentally drag or categorize an infrastructure script into a dissertation volume.

### 7.4 Compliance with Rule 14: Quoted Span Stripping
The regex citation scanner strips all ```` ```code blocks``` ```` and `` `inline code` `` spans prior to indexing, ensuring exhibits and defect logs do not pollute the causality tree.

---

## 8. 📋 IMPLEMENTATION PHASING & SPRINT CHECKLIST

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           DEVELOPMENT IMPLEMENTATION ROADMAP                           │
├─────────┬──────────────────────────────────────────────────────────────────────────────┤
│ PHASE 1 │ Backend Core & Scanner (`genealogy_core.py`, `genealogy_routes.py`)           │
│         │ • Fast SQLite caching of file metadata (mtime, ctime, lines, size, sha256)   │
│         │ • Footnote link scanner and Rule 12 session log parser                       │
│         │ • Unit tests in `tests/test_genealogy_navigator.py`                          │
├─────────┼──────────────────────────────────────────────────────────────────────────────┤
│ PHASE 2 │ Primary Spatial Treemap & Sunburst (`static/modules/genealogy_treemap.js`)    │
│         │ • D3 Squarified Treemap layout with semantic zoom                            │
│         │ • Concentric Sunburst radial partition with center project hub               │
│         │ • Full color semiotics integration with `jarvis.css`                         │
├─────────┼──────────────────────────────────────────────────────────────────────────────┤
│ PHASE 3 │ Causality DAG Engine & Bi-Directional Deck                                   │
│         │ • Dagre layout for derivation pipeline (Books -> Extracts -> Dossiers)       │
│         │ • Split-view synchronization (hovering in Treemap pulses in DAG)             │
│         │ • Click-to-trace ancestral illumination                                      │
├─────────┼──────────────────────────────────────────────────────────────────────────────┤
│ PHASE 4 │ Chrono-Scrubber, Inspector Blade, and Polish                                 │
│         │ • Interactive timeline slider scrubbing July 2026 -> Oct 2026                │
│         │ • Side inspector blade with cryptographic hashes and 1-click VS Code launch   │
│         │ • Automated parity tests and final deployment to CatholicJarvis Suite        │
└─────────┴──────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. 🏛️ CONCLUSION & ARCHITECTURAL VERDICT

James's proposal for a **Tiered Tree Map & Visual Genealogy File Navigator** solves the fundamental cognitive limitation of modern hierarchical file explorers. By unifying **spatial volume** (Treemap), **radial depth** (Sunburst), and **epistemic derivation** (Causality DAG), this system provides an unmatched mental prosthesis for *History Proves Catholicism*. It transforms a sprawling 28M-token multi-vault archive into an intuitive, living, navigable cathedral of theological evidence.

"""Open a book from disk in the read-aloud Studio (Claude GUI, Opus 5.5, 2026-10-07).

GET /api/studio/open?path=...  ->  the same shape /api/upload returns (title, total_pages, pages[{page_num, chunks}]),
plus `label` per section and `path`, so the Studio can open PDFs, EPUBs, Markdown, text and .docx straight from the
Files roots (C:\\Users\\Elation\\PDFS included) without uploading. EPUB chapters become the Studio's "pages", which is
why an EPUB reads cleaner than its PDF: no page numbers or running headers inside sentences.
Read-only; the path must be inside a Files root (files_core.resolve is the boundary)."""
import os
import re

from fastapi import APIRouter, HTTPException, Query

from modules import files_core

router = APIRouter(prefix="/api/studio", tags=["studio"])


def _tools():
    # the cleaning and chunking the Studio already uses for uploads (app.py); imported late to avoid a cycle
    import app as _app
    return _app.clean_pdf_text, _app.chunk_text


def _pages(sections, clean, chunk):
    pages, cid = [], 0
    for n, (label, text) in enumerate(sections, start=1):
        chunks = []
        for para in re.split(r"\n\s*\n", text):
            para = clean(para) if clean else para
            for c in chunk(para):
                if len(c.strip()) > 10:
                    chunks.append({"id": cid, "page": n, "text": c.strip()})
                    cid += 1
        if chunks:
            pages.append({"page_num": n, "label": label, "chunks": chunks})
    return pages, cid


@router.get("/open")
def open_doc(path: str = Query(...)):
    try:
        ap = files_core.resolve(path)
    except files_core.Forbidden as e:
        raise HTTPException(403, str(e))
    if not os.path.isfile(ap):
        raise HTTPException(404, "not found")
    clean, chunk = _tools()
    t = files_core.file_type(ap)
    title = os.path.splitext(os.path.basename(ap))[0].split(" -- ")[0]
    try:
        if t == "pdf":
            import fitz
            doc = fitz.open(ap)
            if doc.metadata and doc.metadata.get("title"):
                title = doc.metadata["title"]
            secs = [(f"Page {i + 1}", doc[i].get_text("text")) for i in range(len(doc))]
            pages, n = _pages([(lab, clean(txt)) for lab, txt in secs], None, chunk)
            for p in pages:
                p["label"] = None                     # the Studio shows "PAGE n" for real pages
            total = len(doc)
        elif t == "epub":
            pages, n = _pages(files_core.epub_sections(ap), None, chunk)
            total = len(pages)
        elif t in ("markdown", "text", "docx"):
            text = files_core.docx_text(ap) if t == "docx" else files_core._read_text(ap)
            parts = re.split(r"(?m)^(#{1,3}\s+.+)$", text)
            secs, cur = [], ("Start", parts[0])
            for k in range(1, len(parts), 2):
                if cur[1].strip():
                    secs.append(cur)
                cur = (re.sub(r"^#+\s*", "", parts[k]).strip(), parts[k + 1] if k + 1 < len(parts) else "")
            if cur[1].strip():
                secs.append(cur)
            pages, n = _pages(secs, None, chunk)
            total = len(pages)
        else:
            raise HTTPException(415, "the Studio reads PDF, EPUB, Markdown, text and .docx files")
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"could not read this file: {type(e).__name__}: {e}")
    return {"title": title, "filename": os.path.basename(ap), "path": ap, "source_type": t,
            "total_pages": total, "readable_pages": len(pages), "total_chunks": n, "pages": pages}

"""
Reader module HTTP routes (module id "reader"). Task C004.
app.py includes this router automatically.

  GET  /api/reader/chapters                  list all 35 chapters
  GET  /api/reader/chapters/{stem}           get chapter HTML, tags, checking items
  GET  /api/reader/checking                  book-wide list of checking items
  GET  /api/reader/tiers/{stem}/{section}    get 3-level tier data for a section
  GET  /api/reader/doc?path=&part=           (C007) any allowed .md/.html document, same structure as a
                                             chapter plus a table of contents ("parts"); html is one part.
                                             403 for any path outside the allowed set.
  GET  /api/reader/docs?q=&limit=            (C007) registry documents + 10_VOLUMES files, to pick from
"""
from fastapi import APIRouter, HTTPException, Query
from . import reader_core as core

router = APIRouter(prefix="/api/reader", tags=["reader"])


@router.get("/chapters")
def list_chapters():
    chapters = core.list_chapters()
    return {"chapters": chapters, "count": len(chapters)}


@router.get("/chapters/{stem}")
def get_chapter(stem: str):
    try:
        return core.get_chapter_data(stem)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Chapter {stem} not found")


@router.get("/checking")
def bookwide_checking():
    items = core.get_bookwide_checking_items()
    return {"items": items, "count": len(items)}


@router.get("/tiers/{stem}/{section}")
def get_tier(stem: str, section: str):
    return core.get_section_tier(stem, section)


@router.get("/doc")
def get_doc(path: str = Query(..., description="absolute path of a document"),
            part: int = Query(0, ge=0, description="which part of a large document to render")):
    try:
        return core.get_doc_data(path, part)
    except core.DocForbidden as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="document not found")
    except core.DocTooLarge as e:
        raise HTTPException(status_code=413, detail=str(e))
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/docs")
def list_docs(q: str = Query("", description="words that must all appear in the title or path"),
              limit: int = Query(40, ge=1, le=200)):
    return core.search_library(q, limit)


@router.get("/dossiers")
def list_dossiers():
    """List subject research dossiers and study guides available for live reading."""
    docs = core.list_dossiers()
    return {"dossiers": docs, "count": len(docs)}


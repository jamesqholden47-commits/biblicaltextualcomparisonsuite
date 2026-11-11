"""
modules/navigator_routes.py — FastAPI REST Routes for File Genealogy & Treemap Navigator
CatholicJarvis Master Work Suite (Port 8080)
"""

import os
import subprocess
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from modules import navigator_core as core

router = APIRouter(prefix="/api/navigator", tags=["navigator"])


class OpenExternalRequest(BaseModel):
    path: str


@router.get("/tree")
def get_tree(
    sort_by: str = Query("mtime", description="Sort by: mtime, ctime, atime, size, lines, citations, name"),
    group_by: str = Query("category", description="Group by: category, academic_tier, temporal_month, folder"),
    size_metric: str = Query("size", description="Size metric: size, lines, citations"),
    root_filter: Optional[str] = Query(None, description="Filter by root folder name"),
    exclude_infrastructure: bool = Query(False, description="Exclude Rule 13 infrastructure files"),
    chrono_max_month: Optional[str] = Query(None, description="Temporal filter up to YYYY-MM")
):
    """Returns hierarchical tree structure for interactive D3/Canvas Treemap & Sunburst."""
    try:
        data = core.get_cached_or_scan()
        return core.build_treemap(
            data,
            sort_by=sort_by,
            group_by=group_by,
            size_metric=size_metric,
            root_filter=root_filter,
            exclude_infrastructure=exclude_infrastructure,
            chrono_max_month=chrono_max_month
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Treemap construction error: {str(e)}")


@router.get("/genealogy")
def get_genealogy(
    file_id: Optional[str] = Query(None, description="Optional center file for ego-network"),
    depth: int = Query(2, ge=1, le=5, description="Search depth for genealogy graph"),
    category: Optional[str] = Query(None, description="Filter nodes by category"),
    exclude_infrastructure: bool = Query(False, description="Exclude Rule 13 infrastructure files"),
    chrono_max_month: Optional[str] = Query(None, description="Temporal filter up to YYYY-MM")
):
    """Returns directed graph nodes and edges representing 'what file caused which file'."""
    try:
        data = core.get_cached_or_scan()
        return core.get_genealogy_graph(
            data,
            file_id=file_id,
            depth=depth,
            category=category,
            exclude_infrastructure=exclude_infrastructure,
            chrono_max_month=chrono_max_month
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Genealogy graph error: {str(e)}")



@router.get("/file-preview")
def get_file_preview(path: str = Query(..., description="Absolute path of file to preview")):
    """Returns file content sample, metadata, upstream parents, and downstream derivative files."""
    try:
        return core.get_file_preview(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview error: {str(e)}")


@router.post("/reindex")
def trigger_reindex():
    """Trigger background re-indexing of filesystem and genealogy links."""
    return core.reindex_async()


@router.get("/status")
def get_status():
    """Returns current indexing state."""
    return core._index_state


@router.post("/open-external")
def open_external(req: OpenExternalRequest):
    """Launch file in native desktop application (Obsidian/VS Code/Notepad)."""
    p = os.path.abspath(req.path)
    if not os.path.exists(p):
        raise HTTPException(status_code=404, detail=f"File not found on disk: {p}")
    try:
        if os.name == "nt":
            os.startfile(p)  # noqa: S606
        else:
            subprocess.Popen(["xdg-open", p])
        return {"success": True, "message": f"Opened {os.path.basename(p)}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open file externally: {str(e)}")

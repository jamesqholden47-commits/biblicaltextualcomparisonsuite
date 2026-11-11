"""
Vatican Curial Intel, Religious Orders & Scholarly Journals HTTP Routes (module id "vatican_culture").
Included automatically in CatholicJarvis Master Work Suite via modules/*_routes.py discovery.

Endpoints:
  GET /api/vatican-culture/overview    Returns overview metadata and section counts
  GET /api/vatican-culture/orders      Returns tracked religious orders, Roman houses, charisms
  GET /api/vatican-culture/journals    Returns scholarly journals & Vatican gazettes with filter
  GET /api/vatican-culture/bookshelf   Returns what the Curia & Magisterium are reading
  GET /api/vatican-culture/debates     Returns active Roman theological & philosophical debates
  GET /api/vatican-culture/feed        Returns curated live curial news and intellectual essays
  GET /api/vatican-culture/all         Returns complete master culture intelligence dataset
"""

from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from . import vatican_culture_core as core

router = APIRouter(prefix="", tags=["vatican_culture"])


@router.get("/api/vatican-culture/overview")
def get_culture_overview():
    """Return overview summary and counts across all curial intellectual domains."""
    data = core.get_culture_data()
    return {
        "metadata": data.get("metadata", {}),
        "counts": {
            "orders": len(data.get("orders", [])),
            "journals": len(data.get("journals", [])),
            "bookshelf": len(data.get("curial_bookshelf", [])),
            "debates": len(data.get("curial_debates", [])),
            "news_items": len(data.get("curial_news_feed", []))
        }
    }


@router.get("/api/vatican-culture/orders")
def get_religious_orders(query: Optional[str] = Query(None)):
    """Return tracked religious orders and Roman intellectual houses."""
    orders = core.get_orders()
    if query:
        q = query.lower()
        orders = [
            o for o in orders
            if q in o.get("name", "").lower()
            or q in o.get("acronym", "").lower()
            or q in o.get("charism", "").lower()
            or any(q in h.get("name", "").lower() for h in o.get("pontifical_academic_houses", []))
        ]
    return {"count": len(orders), "orders": orders}


@router.get("/api/vatican-culture/journals")
def get_scholarly_journals(order: Optional[str] = Query(None), query: Optional[str] = Query(None)):
    """Return scholarly theological and hagiographical journals with filter."""
    journals = core.get_journals(order)
    if query:
        q = query.lower()
        journals = [
            j for j in journals
            if q in j.get("title", "").lower()
            or q in j.get("publisher", "").lower()
            or q in j.get("curial_status", "").lower()
            or q in j.get("current_focus_2026", "").lower()
        ]
    return {"count": len(journals), "journals": journals}


@router.get("/api/vatican-culture/bookshelf")
def get_curial_bookshelf():
    """Return the Curial Bookshelf: the books the Magisterium is reading right now."""
    books = core.get_bookshelf()
    return {"count": len(books), "bookshelf": books}


@router.get("/api/vatican-culture/debates")
def get_curial_debates():
    """Return high-priority theological, philosophical, and diplomatic debates in Rome."""
    debates = core.get_debates()
    return {"count": len(debates), "debates": debates}


@router.get("/api/vatican-culture/feed")
def get_curial_feed(category: Optional[str] = Query(None)):
    """Return curated live news, essays, and intellectual dispatches from Rome."""
    items = core.get_news_feed(category)
    return {"count": len(items), "items": items}


@router.get("/api/vatican-culture/all")
def get_all_culture_data():
    """Return complete master dataset for the Vatican Intel & Curial Culture Portal."""
    return core.get_culture_data()

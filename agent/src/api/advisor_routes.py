"""REST surface for the advisor: push holdings, review, decide, track."""
from __future__ import annotations

import asyncio
import threading
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query

from src.advisor.models import DecisionIn, HoldingsIn, ReviewRequest
from src.advisor.service import AdvisorError, AdvisorService
from src.api.security import require_auth

_service: AdvisorService | None = None
_lock = threading.Lock()


def get_service() -> AdvisorService:
    global _service
    with _lock:
        if _service is None:
            _service = AdvisorService()
        return _service


def _run(fn, *args):
    try:
        return fn(*args)
    except AdvisorError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


def _public(review: dict[str, Any]) -> dict[str, Any]:
    """The advised book is tracker state, not something the app renders."""
    return {k: v for k, v in review.items() if k != "hypothetical_book"}


def register_advisor_routes(app: FastAPI) -> None:
    auth = [Depends(require_auth)]

    @app.post("/advisor/holdings", dependencies=auth)
    async def push_holdings(payload: HoldingsIn) -> dict[str, Any]:
        return {"status": "ok", **await asyncio.to_thread(_run, get_service().push_holdings, payload)}

    @app.get("/advisor/holdings/latest", dependencies=auth)
    async def latest_holdings() -> dict[str, Any]:
        return {"status": "ok", "snapshot": _run(get_service().latest_holdings)}

    @app.post("/advisor/review", dependencies=auth)
    async def run_review(payload: ReviewRequest | None = None) -> dict[str, Any]:
        review = await asyncio.to_thread(_run, get_service().review, payload or ReviewRequest())
        return {"status": "ok", "review": _public(review)}

    @app.get("/advisor/reviews", dependencies=auth)
    async def list_reviews(limit: int = Query(20, ge=1, le=200)) -> dict[str, Any]:
        return {"status": "ok", "reviews": [_public(r) for r in get_service().store.list_reviews(limit)]}

    @app.get("/advisor/reviews/{review_id}", dependencies=auth)
    async def get_review(review_id: str) -> dict[str, Any]:
        store = get_service().store
        review = store.get_review(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="review not found")
        return {"status": "ok", "review": {**_public(review), "recommendations": store.list_recommendations(review_id=review_id)}}

    @app.get("/advisor/recommendations", dependencies=auth)
    async def list_recommendations(status: str | None = Query(None, pattern="^(open|accepted|rejected)$"),
                                   review_id: str | None = None,
                                   limit: int = Query(200, ge=1, le=1000)) -> dict[str, Any]:
        recs = get_service().store.list_recommendations(status=status, review_id=review_id, limit=limit)
        return {"status": "ok", "recommendations": recs}

    @app.post("/advisor/recommendations/{rec_id}/decision", dependencies=auth)
    async def decide(rec_id: str, payload: DecisionIn) -> dict[str, Any]:
        return {"status": "ok", "recommendation": _run(get_service().decide, rec_id, payload)}

    @app.get("/advisor/performance", dependencies=auth)
    async def performance(review_id: str | None = None, limit: int = Query(20, ge=1, le=100)) -> dict[str, Any]:
        return {"status": "ok", **await asyncio.to_thread(_run, get_service().performance, review_id, limit)}

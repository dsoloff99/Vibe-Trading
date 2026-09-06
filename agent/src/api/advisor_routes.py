"""REST surface for the advisor: push holdings, review, decide, track."""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query

from src.advisor.models import DecisionIn, HoldingsIn, ReviewRequest
from src.advisor.service import AdvisorError, AdvisorService
from src.advisor.tracker import review_performance, scorecard
from src.api.security import require_auth

_service: AdvisorService | None = None


def get_service() -> AdvisorService:
    global _service
    if _service is None:
        _service = AdvisorService()
    return _service


def _run(fn, *args):
    try:
        return fn(*args)
    except AdvisorError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


def register_advisor_routes(app: FastAPI) -> None:
    auth = [Depends(require_auth)]

    @app.post("/advisor/holdings", dependencies=auth)
    async def push_holdings(payload: HoldingsIn) -> dict[str, Any]:
        svc = get_service()
        return {"status": "ok", **await asyncio.to_thread(_run, svc.push_holdings, payload)}

    @app.get("/advisor/holdings/latest", dependencies=auth)
    async def latest_holdings() -> dict[str, Any]:
        return {"status": "ok", "snapshot": _run(get_service().latest_holdings)}

    @app.post("/advisor/review", dependencies=auth)
    async def run_review(payload: ReviewRequest | None = None) -> dict[str, Any]:
        svc = get_service()
        review = await asyncio.to_thread(_run, svc.review, payload or ReviewRequest())
        return {"status": "ok", "review": review}

    @app.get("/advisor/reviews", dependencies=auth)
    async def list_reviews(limit: int = Query(20, ge=1, le=200)) -> dict[str, Any]:
        svc = get_service()
        reviews = svc.store.list_reviews(limit)
        return {"status": "ok", "reviews": [{k: v for k, v in r.items() if k != "hypothetical_book"} for r in reviews]}

    @app.get("/advisor/reviews/{review_id}", dependencies=auth)
    async def get_review(review_id: str) -> dict[str, Any]:
        svc = get_service()
        review = svc.store.get_review(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="review not found")
        return {"status": "ok", "review": {**review, "recommendations": svc.store.list_recommendations(review_id=review_id)}}

    @app.get("/advisor/recommendations", dependencies=auth)
    async def list_recommendations(status: str | None = Query(None, pattern="^(open|accepted|rejected|expired)$"),
                                   review_id: str | None = None,
                                   limit: int = Query(200, ge=1, le=1000)) -> dict[str, Any]:
        recs = get_service().store.list_recommendations(status=status, review_id=review_id, limit=limit)
        return {"status": "ok", "recommendations": recs}

    @app.post("/advisor/recommendations/{rec_id}/decision", dependencies=auth)
    async def decide(rec_id: str, payload: DecisionIn) -> dict[str, Any]:
        return {"status": "ok", "recommendation": _run(get_service().decide, rec_id, payload)}

    @app.get("/advisor/performance", dependencies=auth)
    async def performance(review_id: str | None = None, limit: int = Query(20, ge=1, le=100)) -> dict[str, Any]:
        svc = get_service()

        def _compute() -> dict[str, Any]:
            reviews = [svc.store.get_review(review_id)] if review_id else svc.store.list_reviews(limit)
            if review_id and not reviews[0]:
                raise AdvisorError("review not found", 404)
            per_review = []
            for review in reviews:
                snapshot = svc.store.get_snapshot(review["snapshot_id"]) or {"accounts": []}
                recs = svc.store.list_recommendations(review_id=review["id"])
                per_review.append(review_performance(review, snapshot, recs, svc.today(), svc._fetch))
            return {"scorecard": scorecard(per_review), "reviews": per_review}

        return {"status": "ok", **await asyncio.to_thread(_run, _compute)}

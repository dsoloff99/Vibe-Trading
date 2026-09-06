"""SQLite persistence for holdings snapshots, reviews and recommendations."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from src.config.paths import get_runtime_root

_SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    source TEXT NOT NULL,
    as_of TEXT,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snapshots_created ON snapshots(created_at DESC);

CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
    model TEXT,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reviews_created ON reviews(created_at DESC);

CREATE TABLE IF NOT EXISTS recommendations (
    id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL REFERENCES reviews(id),
    created_at TEXT NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    decided_at TEXT,
    note TEXT,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_recs_review ON recommendations(review_id);
CREATE INDEX IF NOT EXISTS idx_recs_status ON recommendations(status, created_at DESC);
"""


def _dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str)


class AdvisorStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (get_runtime_root() / "advisor" / "advisor.sqlite3")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db, db:
            db.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    # ── snapshots ─────────────────────────────────────────────────────────
    def save_snapshot(self, snapshot: dict[str, Any]) -> None:
        with closing(self._connect()) as db, db:
            db.execute(
                "INSERT INTO snapshots (id, created_at, source, as_of, payload) VALUES (?,?,?,?,?)",
                (snapshot["id"], snapshot["created_at"], snapshot.get("source", ""),
                 snapshot.get("as_of"), _dumps(snapshot)),
            )

    def get_snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as db, db:
            row = db.execute("SELECT payload FROM snapshots WHERE id=?", (snapshot_id,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def latest_snapshot(self) -> dict[str, Any] | None:
        with closing(self._connect()) as db, db:
            row = db.execute("SELECT payload FROM snapshots ORDER BY created_at DESC LIMIT 1").fetchone()
        return json.loads(row["payload"]) if row else None

    # ── reviews ───────────────────────────────────────────────────────────
    def save_review(self, review: dict[str, Any], recommendations: list[dict[str, Any]]) -> None:
        with closing(self._connect()) as db, db:
            db.execute(
                "INSERT INTO reviews (id, created_at, snapshot_id, model, payload) VALUES (?,?,?,?,?)",
                (review["id"], review["created_at"], review["snapshot_id"], review.get("model"), _dumps(review)),
            )
            db.executemany(
                "INSERT INTO recommendations (id, review_id, created_at, symbol, action, status, payload) "
                "VALUES (?,?,?,?,?,?,?)",
                [(r["id"], review["id"], r["created_at"], r["symbol"], r["action"], r.get("status", "open"), _dumps(r))
                 for r in recommendations],
            )

    def get_review(self, review_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as db, db:
            row = db.execute("SELECT payload FROM reviews WHERE id=?", (review_id,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def list_reviews(self, limit: int = 50) -> list[dict[str, Any]]:
        with closing(self._connect()) as db, db:
            rows = db.execute("SELECT payload FROM reviews ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    # ── recommendations ───────────────────────────────────────────────────
    def list_recommendations(self, *, status: str | None = None, review_id: str | None = None,
                             limit: int = 200) -> list[dict[str, Any]]:
        sql = "SELECT payload, status, decided_at, note FROM recommendations"
        clauses, args = [], []
        if status:
            clauses.append("status=?")
            args.append(status)
        if review_id:
            clauses.append("review_id=?")
            args.append(review_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at DESC LIMIT ?"
        args.append(limit)
        with closing(self._connect()) as db, db:
            rows = db.execute(sql, args).fetchall()
        out = []
        for r in rows:
            rec = json.loads(r["payload"])
            rec.update({"status": r["status"], "decided_at": r["decided_at"], "note": r["note"]})
            out.append(rec)
        return out

    def get_recommendation(self, rec_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as db, db:
            r = db.execute("SELECT payload, status, decided_at, note FROM recommendations WHERE id=?", (rec_id,)).fetchone()
        if not r:
            return None
        rec = json.loads(r["payload"])
        rec.update({"status": r["status"], "decided_at": r["decided_at"], "note": r["note"]})
        return rec

    def decide(self, rec_id: str, status: str, note: str, decided_at: str) -> dict[str, Any] | None:
        with closing(self._connect()) as db, db:
            cur = db.execute(
                "UPDATE recommendations SET status=?, note=?, decided_at=? WHERE id=?",
                (status, note, decided_at, rec_id),
            )
            if cur.rowcount == 0:
                return None
        return self.get_recommendation(rec_id)

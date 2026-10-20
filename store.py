"""SQLite persistence layer for Jarvis MVP."""
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

DB_PATH = os.getenv("DATABASE_PATH", "jarvis.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db():
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
            title TEXT NOT NULL, body TEXT NOT NULL,
            sources_json TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT NOT NULL,
            body TEXT NOT NULL, sources_json TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL)""")


def add_note(kind, title, body, sources=None):
    with _connect() as conn:
        cur = conn.execute("INSERT INTO notes(kind,title,body,sources_json,created_at) VALUES(?,?,?,?,?)",
                           (kind, title, body, json.dumps(sources or [], ensure_ascii=False), _now()))
        return int(cur.lastrowid)


def recent_notes(limit=8):
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM notes ORDER BY id DESC LIMIT ?", (max(1, min(limit, 25)),)).fetchall()
    return [dict(r) | {"sources": json.loads(r["sources_json"])} for r in rows]


def search_notes(query, limit=6):
    terms = [t.strip() for t in query.split() if len(t.strip()) > 2][:8]
    if not terms:
        return []
    where = " OR ".join("(title LIKE ? OR body LIKE ?)" for _ in terms)
    params = []
    for term in terms:
        params.extend([f"%{term}%", f"%{term}%"])
    params.append(max(1, min(limit, 10)))
    with _connect() as conn:
        rows = conn.execute(f"SELECT * FROM notes WHERE {where} ORDER BY id DESC LIMIT ?", params).fetchall()
    return [dict(r) | {"sources": json.loads(r["sources_json"])} for r in rows]


def add_draft(topic, body, sources=None):
    now = _now()
    with _connect() as conn:
        cur = conn.execute("INSERT INTO drafts(topic,body,sources_json,status,created_at,updated_at) VALUES(?,?,?,'draft',?,?)",
                           (topic, body, json.dumps(sources or [], ensure_ascii=False), now, now))
        return int(cur.lastrowid)


def get_draft(draft_id):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
    return dict(row) | {"sources": json.loads(row["sources_json"])} if row else None


def recent_drafts(limit=8):
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM drafts ORDER BY id DESC LIMIT ?", (max(1, min(limit, 25)),)).fetchall()
    return [dict(r) | {"sources": json.loads(r["sources_json"])} for r in rows]


def set_draft_status(draft_id, status):
    if status not in {"draft", "approved", "rejected"}:
        raise ValueError("Unsupported draft status")
    with _connect() as conn:
        cur = conn.execute("UPDATE drafts SET status=?, updated_at=? WHERE id=?", (status, _now(), draft_id))
        return cur.rowcount == 1

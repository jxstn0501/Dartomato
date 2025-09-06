import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data.db"

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ingests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT (datetime('now')),
                filename TEXT,
                player_names TEXT,
                bust INTEGER,
                meta_json TEXT,
                raw_json TEXT,
                normalized_json TEXT
            )
        """)
        conn.commit()

def insert_ingest(filename: str, player_names: List[str], bust: bool, meta: Dict[str, Any], raw: Dict[str, Any], normalized: Dict[str, Any]) -> int:
    with _get_conn() as conn:
        cur = conn.execute("""            INSERT INTO ingests (filename, player_names, bust, meta_json, raw_json, normalized_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            filename,
            json.dumps(player_names, ensure_ascii=False),
            1 if bust else 0,
            json.dumps(meta or {}, ensure_ascii=False),
            json.dumps(raw, ensure_ascii=False),
            json.dumps(normalized, ensure_ascii=False),
        ))
        conn.commit()
        return cur.lastrowid

def list_ingests(limit: int=50) -> List[Dict[str, Any]]:
    with _get_conn() as conn:
        rows = conn.execute("SELECT id, created_at, filename, player_names, bust FROM ingests ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            out.append({
                "id": r["id"],
                "created_at": r["created_at"],
                "filename": r["filename"],
                "player_names": json.loads(r["player_names"] or "[]"),
                "bust": bool(r["bust"]),
            })
        return out

def get_ingest(ingest_id: int) -> Optional[Dict[str, Any]]:
    with _get_conn() as conn:
        r = conn.execute("SELECT * FROM ingests WHERE id = ?", (ingest_id,)).fetchone()
        if not r:
            return None
        return {
            "id": r["id"],
            "created_at": r["created_at"],
            "filename": r["filename"],
            "player_names": json.loads(r["player_names"] or "[]"),
            "bust": bool(r["bust"]),
            "meta": json.loads(r["meta_json"] or "{}"),
            "raw": json.loads(r["raw_json"] or "{}"),
            "normalized": json.loads(r["normalized_json"] or "{}"),
        }

def delete_ingest(ingest_id: int) -> bool:
    with _get_conn() as conn:
        cur = conn.execute("DELETE FROM ingests WHERE id = ?", (ingest_id,))
        conn.commit()
        return cur.rowcount > 0

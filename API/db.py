import json
import sqlite3
import secrets
from pathlib import Path
from datetime import datetime, timedelta, UTC
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "api.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

@contextmanager
def _connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db() -> None:
    with _connect() as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS creator_tokens (
                user_id    TEXT NOT NULL,
                platform   TEXT NOT NULL,
                token_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, platform)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS oauth_states (
                state      TEXT PRIMARY KEY,
                user_id    TEXT NOT NULL,
                platform   TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
    purge_states()

def save_token(user_id: str, platform: str, token: dict) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO creator_tokens (user_id, platform, token_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, platform)
            DO UPDATE SET token_json = excluded.token_json,
                          updated_at = excluded.updated_at
            """,
            (user_id, platform, json.dumps(token), datetime.now(UTC).isoformat()),
        )

def get_token(user_id: str, platform: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT token_json FROM creator_tokens WHERE user_id = ? AND platform = ?",
            (user_id, platform),
        ).fetchone()
    return json.loads(row["token_json"]) if row else None

def create_state(user_id: str, platform: str) -> str:
    purge_states()
    state = secrets.token_urlsafe(32)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO oauth_states (state, user_id, platform, created_at) VALUES (?, ?, ?, ?)",
            (state, user_id, platform, datetime.now(UTC).isoformat()),
        )
    return state

def consume_state(state: str) -> tuple[str, str] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT user_id, platform FROM oauth_states WHERE state = ?",
            (state,),
        ).fetchone()
        if row is None:
            return None
        conn.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
    return row["user_id"], row["platform"]


def purge_states(max_age_minutes: int = 10) -> int:
    cutoff = (datetime.now(UTC) - timedelta(minutes=max_age_minutes)).isoformat()
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM oauth_states WHERE created_at < ?", (cutoff,)
        )
        return cur.rowcount

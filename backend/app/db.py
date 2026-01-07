import sqlite3
from typing import Optional, Any, Dict
from .config import DB_PATH

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS tokens (
          id INTEGER PRIMARY KEY CHECK (id = 1),
          athlete_id INTEGER NOT NULL,
          access_token TEXT NOT NULL,
          refresh_token TEXT NOT NULL,
          expires_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sync_state (
          id INTEGER PRIMARY KEY CHECK (id = 1),
          last_sync INTEGER NOT NULL
        );

        -- Derived summaries only
        CREATE TABLE IF NOT EXISTS summaries (
          period_type TEXT NOT NULL,      -- 'week' | 'month' | 'year'
          period_start TEXT NOT NULL,     -- ISO date YYYY-MM-DD
          run_count INTEGER NOT NULL,
          total_meters REAL NOT NULL,
          total_seconds REAL NOT NULL,
          avg_hr_time_weighted REAL,      -- nullable
          elevation_gain REAL NOT NULL,
          PRIMARY KEY (period_type, period_start)
        );
        """)

def upsert_tokens(athlete_id: int, access_token: str, refresh_token: str, expires_at: int) -> None:
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO tokens (id, athlete_id, access_token, refresh_token, expires_at)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          athlete_id=excluded.athlete_id,
          access_token=excluded.access_token,
          refresh_token=excluded.refresh_token,
          expires_at=excluded.expires_at
        """, (athlete_id, access_token, refresh_token, expires_at))

def get_tokens() -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tokens WHERE id=1").fetchone()
        return dict(row) if row else None

def get_last_sync() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT last_sync FROM sync_state WHERE id=1").fetchone()
        if not row:
            conn.execute("INSERT INTO sync_state (id, last_sync) VALUES (1, 0)")
            return 0
        return int(row["last_sync"])

def set_last_sync(ts: int) -> None:
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO sync_state (id, last_sync) VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET last_sync=excluded.last_sync
        """, (ts,))

def upsert_summary(period_type: str, period_start: str, run_count: int,
                   total_meters: float, total_seconds: float,
                   avg_hr_time_weighted: Optional[float],
                   elevation_gain: float) -> None:
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO summaries
          (period_type, period_start, run_count, total_meters, total_seconds, avg_hr_time_weighted, elevation_gain)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(period_type, period_start) DO UPDATE SET
          run_count=excluded.run_count,
          total_meters=excluded.total_meters,
          total_seconds=excluded.total_seconds,
          avg_hr_time_weighted=excluded.avg_hr_time_weighted,
          elevation_gain=excluded.elevation_gain
        """, (period_type, period_start, run_count, total_meters, total_seconds, avg_hr_time_weighted, elevation_gain))

def fetch_summaries(period_type: str):
    with get_conn() as conn:
        rows = conn.execute("""
          SELECT * FROM summaries
          WHERE period_type=?
          ORDER BY period_start DESC
        """, (period_type,)).fetchall()
        return [dict(r) for r in rows]

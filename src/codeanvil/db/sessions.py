import sqlite3
from typing import Optional

from codeanvil.config.logger import get_logger

log = get_logger(__name__)


def create_session(conn: sqlite3.Connection, project_id: int) -> int:
    cur = conn.execute(
        "INSERT INTO sessions (project_id) VALUES (?)", (project_id,)
    )
    conn.commit()
    log.info("created session %d for project %d", cur.lastrowid, project_id)
    return cur.lastrowid


def get_session(conn: sqlite3.Connection, session_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()


def list_sessions(conn: sqlite3.Connection, project_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM sessions WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,),
    ).fetchall()


def update_gate(conn: sqlite3.Connection, session_id: int, gate: str) -> None:
    conn.execute(
        "UPDATE sessions SET current_gate = ?, updated_at = datetime('now') WHERE id = ?",
        (gate, session_id),
    )
    conn.commit()
    log.info("session %d advanced to %s", session_id, gate)


def record_gate_result(
    conn: sqlite3.Connection, session_id: int, gate: str, passed: bool, report: str = ""
) -> None:
    conn.execute(
        "INSERT INTO gate_results (session_id, gate, passed, report) VALUES (?, ?, ?, ?)",
        (session_id, gate, int(passed), report),
    )
    conn.commit()
    log.info("gate %s %s for session %d", gate, "PASSED" if passed else "FAILED", session_id)

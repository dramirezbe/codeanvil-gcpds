import sqlite3


def list_sessions(conn: sqlite3.Connection, project_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM sessions WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,),
    ).fetchall()

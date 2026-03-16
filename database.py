"""SQLite DAO layer for Cairn."""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

def _get_db_dir() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "cairn"
    return Path.home() / ".local" / "share" / "cairn"

DB_DIR = _get_db_dir()
DB_PATH = DB_DIR / "tasks.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    name                      TEXT NOT NULL,
    project                   TEXT NOT NULL DEFAULT '',
    deadline                  TEXT,
    reminder                  INTEGER NOT NULL DEFAULT 0,
    completed                 INTEGER NOT NULL DEFAULT 0,
    created_at                TEXT NOT NULL,
    completed_at              TEXT,
    reminder_interval_hours   INTEGER,  -- NULL = use global setting
    reminder_active_days      TEXT,     -- NULL = use global setting; else "0,1,2,3,4"
    reminder_hour             INTEGER,  -- NULL = use global setting
    reminder_minute           INTEGER   -- NULL = use global setting
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
"""

DEFAULT_SETTINGS = {
    "reminder_hour": "8",
    "reminder_minute": "0",
    "reminder_interval_hours": "0",       # 0 = once per day
    "reminder_active_days": "0,1,2,3,4",  # Mon–Fri (0=Mon … 6=Sun)
}


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        # Migrate: add override columns to existing tasks table if absent
        existing = {row[1] for row in conn.execute("PRAGMA table_info(tasks)")}
        for col, definition in [
            ("reminder_interval_hours", "INTEGER"),
            ("reminder_active_days", "TEXT"),
            ("reminder_hour", "INTEGER"),
            ("reminder_minute", "INTEGER"),
        ]:
            if col not in existing:
                conn.execute(f"ALTER TABLE tasks ADD COLUMN {col} {definition}")


# --- Task CRUD ---

def get_active_tasks() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE completed=0 ORDER BY created_at DESC"
        ).fetchall()


def get_completed_tasks() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE completed=1 ORDER BY completed_at DESC"
        ).fetchall()


def get_reminder_tasks() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE reminder=1 AND completed=0"
        ).fetchall()


def create_task(
    name: str,
    project: str,
    deadline: str | None,
    reminder: bool,
    reminder_interval_hours: int | None = None,
    reminder_active_days: str | None = None,
    reminder_hour: int | None = None,
    reminder_minute: int | None = None,
) -> int:
    now = datetime.now().isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (name, project, deadline, reminder, completed, created_at, "
            "reminder_interval_hours, reminder_active_days, reminder_hour, reminder_minute) "
            "VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?)",
            (name, project, deadline, int(reminder), now,
             reminder_interval_hours, reminder_active_days, reminder_hour, reminder_minute),
        )
        return cur.lastrowid


def update_task(
    task_id: int,
    name: str,
    project: str,
    deadline: str | None,
    reminder: bool,
    reminder_interval_hours: int | None = None,
    reminder_active_days: str | None = None,
    reminder_hour: int | None = None,
    reminder_minute: int | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET name=?, project=?, deadline=?, reminder=?, "
            "reminder_interval_hours=?, reminder_active_days=?, "
            "reminder_hour=?, reminder_minute=? WHERE id=?",
            (name, project, deadline, int(reminder),
             reminder_interval_hours, reminder_active_days,
             reminder_hour, reminder_minute, task_id),
        )


def complete_task(task_id: int) -> None:
    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET completed=1, completed_at=? WHERE id=?",
            (now, task_id),
        )


def uncomplete_task(task_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET completed=0, completed_at=NULL WHERE id=?",
            (task_id,),
        )


def delete_task(task_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))


# --- Projects ---

def get_projects() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT name FROM projects ORDER BY name COLLATE NOCASE").fetchall()
        return [r["name"] for r in rows]


def create_project(name: str) -> None:
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO projects (name) VALUES (?)", (name,))


def delete_project(name: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM projects WHERE name=?", (name,))


# --- Settings ---

def get_setting(key: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None


def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )


def get_reminder_time() -> tuple[int, int]:
    hour = int(get_setting("reminder_hour") or DEFAULT_SETTINGS["reminder_hour"])
    minute = int(get_setting("reminder_minute") or DEFAULT_SETTINGS["reminder_minute"])
    return hour, minute


def get_reminder_interval_hours() -> int:
    return int(get_setting("reminder_interval_hours") or DEFAULT_SETTINGS["reminder_interval_hours"])


def get_reminder_active_days() -> set[int]:
    raw = get_setting("reminder_active_days") or DEFAULT_SETTINGS["reminder_active_days"]
    return {int(d) for d in raw.split(",") if d.strip().isdigit()}

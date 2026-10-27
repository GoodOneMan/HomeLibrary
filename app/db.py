from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH: Path = Path(__file__).resolve().parent.parent / "library.db"

SCHEMA_SQL: str = """
CREATE TABLE IF NOT EXISTS books (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    author TEXT    NOT NULL CHECK (length(trim(author)) > 0),
    title  TEXT    NOT NULL CHECK (length(trim(title)) > 0),
    year   INTEGER NOT NULL CHECK (year BETWEEN 0 AND 2100),
    genre  TEXT    NOT NULL CHECK (length(trim(genre)) > 0),
    UNIQUE (author, title, year)
);

CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_books_genre  ON books(genre);
CREATE INDEX IF NOT EXISTS idx_books_year   ON books(year);
CREATE INDEX IF NOT EXISTS idx_books_title  ON books(title);
"""


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Возвращает соединение с SQLite с включённым row_factory."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Path | str = DB_PATH) -> None:
    """Создаёт таблицу `books` и индексы, если их нет."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


@contextmanager
def db_cursor(db_path: Path | str = DB_PATH) -> Iterator[sqlite3.Cursor]:
    """Контекстный менеджер: соединение + commit/rollback + close."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
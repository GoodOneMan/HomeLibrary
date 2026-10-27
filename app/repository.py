from __future__ import annotations

from pathlib import Path
from typing import Any

from .db import DB_PATH, db_cursor
from .models import Book


class DuplicateBookError(Exception):
    """Попытка вставить дубликат (author, title, year)."""

class BookRepository:
    """Репозиторий книг поверх SQLite."""

    def __init__(self, db_path: Path | str = DB_PATH) -> None:
        self.db_path = db_path

    # ---------- CREATE ----------
    def add(self, book: Book) -> int:
        """Добавляет книгу и возвращает её id."""
        try:
            with db_cursor(self.db_path) as cur:
                cur.execute(
                    "INSERT INTO books (author, title, year, genre) "
                    "VALUES (?, ?, ?, ?)",
                    (book.author.strip(), book.title.strip(),
                     book.year, book.genre.strip()),
                )
                return int(cur.lastrowid)
        except Exception as exc:
            if "UNIQUE" in str(exc):
                raise DuplicateBookError(
                    f"Книга уже есть: {book.author} — {book.title} ({book.year})"
                ) from exc
            raise

    # ---------- READ ----------
    def get(self, book_id: int) -> Book | None:
        """Возвращает книгу по id или None."""
        with db_cursor(self.db_path) as cur:
            cur.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            row = cur.fetchone()
            return Book.from_row(row) if row else None

    def list_all(self, order_by: str = "author") -> list[Book]:
        """Возвращает все книги с сортировкой."""
        allowed = {"author", "title", "year", "genre"}
        if order_by not in allowed:
            order_by = "author"
        with db_cursor(self.db_path) as cur:
            cur.execute(f"SELECT * FROM books ORDER BY {order_by} COLLATE NOCASE")
            return [Book.from_row(r) for r in cur.fetchall()]

    def search(
        self,
        author: str | None = None,
        title: str | None = None,
        genre: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        order_by: str = "author",
    ) -> list[Book]:
        """Поиск с частичным совпадением (LIKE) и фильтром по году."""
        allowed = {"author", "title", "year", "genre"}
        if order_by not in allowed:
            order_by = "author"

        clauses: list[str] = []
        params: list[Any] = []
        if author:
            clauses.append("author LIKE ?")
            params.append(f"%{author}%")
        if title:
            clauses.append("title LIKE ?")
            params.append(f"%{title}%")
        if genre:
            clauses.append("genre LIKE ?")
            params.append(f"%{genre}%")
        if year_from is not None:
            clauses.append("year >= ?")
            params.append(year_from)
        if year_to is not None:
            clauses.append("year <= ?")
            params.append(year_to)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM books {where} ORDER BY {order_by} COLLATE NOCASE"
        with db_cursor(self.db_path) as cur:
            cur.execute(sql, params)
            return [Book.from_row(r) for r in cur.fetchall()]

    # ---------- UPDATE ----------
    def update(self, book_id: int, **fields: Any) -> Book:
        """Обновляет книгу по id и возвращает новую версию."""
        existing = self.get(book_id)
        if existing is None:
            raise ValueError(f"Книга с id={book_id} не найдена.")
        merged = Book(
            id=book_id,
            author=fields.get("author", existing.author),
            title=fields.get("title", existing.title),
            year=fields.get("year", existing.year),
            genre=fields.get("genre", existing.genre),
        )
        with db_cursor(self.db_path) as cur:
            cur.execute(
                "UPDATE books SET author=?, title=?, year=?, genre=? WHERE id=?",
                (merged.author, merged.title, merged.year, merged.genre, book_id),
            )
        return merged

    # ---------- DELETE ----------
    def delete(self, book_id: int) -> bool:
        """Удаляет книгу по id. Возвращает True, если строка удалена."""
        with db_cursor(self.db_path) as cur:
            cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
            return cur.rowcount > 0

    # ---------- STATISTICS ----------
    def stats_by_genre(self) -> list[tuple[str, int]]:
        """Количество книг по жанрам (по убыванию)."""
        with db_cursor(self.db_path) as cur:
            cur.execute(
                "SELECT genre, COUNT(*) FROM books "
                "GROUP BY genre ORDER BY COUNT(*) DESC"
            )
            return [(r[0], int(r[1])) for r in cur.fetchall()]

    def stats_by_author(self) -> list[tuple[str, int]]:
        """Количество книг по авторам (по убыванию)."""
        with db_cursor(self.db_path) as cur:
            cur.execute(
                "SELECT author, COUNT(*) FROM books "
                "GROUP BY author ORDER BY COUNT(*) DESC"
            )
            return [(r[0], int(r[1])) for r in cur.fetchall()]

    def stats_by_decade(self) -> list[tuple[str, int]]:
        """Распределение по десятилетиям (например, '1990-е')."""
        with db_cursor(self.db_path) as cur:
            cur.execute(
                "SELECT (year / 10) * 10 AS dec, COUNT(*) FROM books "
                "GROUP BY dec ORDER BY dec"
            )
            return [(f"{r[0]}-е", int(r[1])) for r in cur.fetchall()]
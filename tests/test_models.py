"""Тесты модели Book и валидации."""
from __future__ import annotations

import pytest

from app.models import Book, ValidationError


def test_valid_book_ok() -> None:
    """Корректная книга создаётся без ошибок."""
    b = Book(author="Лев Толстой", title="Война и мир", year=1869, genre="роман")
    assert b.year == 1869
    assert b.id is None


@pytest.mark.parametrize(
    "author,title,year,genre",
    [
        ("", "X", 2000, "роман"),
        ("A", "   ", 2000, "роман"),
        ("A", "X", 2000, ""),
        ("A", "X", -1, "роман"),
        ("A", "X", 3000, "роман"),
    ],
)
def test_invalid_book_raises(
    author: str, title: str, year: int, genre: str
) -> None:
    """Некорректные поля вызывают ValidationError."""
    with pytest.raises(ValidationError):
        Book(author=author, title=title, year=year, genre=genre)


def test_year_must_be_int() -> None:
    """Строковый год недопустим."""
    with pytest.raises(ValidationError):
        Book(author="A", title="X", year="2000", genre="роман")  # type: ignore[arg-type]
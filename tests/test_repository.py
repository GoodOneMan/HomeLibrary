"""Тесты репозитория: CRUD, поиск, статистика."""
from __future__ import annotations

import pytest

from app.models import Book
from app.repository import BookRepository, DuplicateBookError


def _mk(author: str = "A", title: str = "T", year: int = 2000,
        genre: str = "G") -> Book:
    return Book(author=author, title=title, year=year, genre=genre)


def test_add_and_get(repo: BookRepository) -> None:
    bid = repo.add(_mk())
    b = repo.get(bid)
    assert b is not None
    assert b.author == "A"
    assert b.id == bid


def test_duplicate_raises(repo: BookRepository) -> None:
    repo.add(_mk())
    with pytest.raises(DuplicateBookError):
        repo.add(_mk())


def test_delete(repo: BookRepository) -> None:
    bid = repo.add(_mk())
    assert repo.delete(bid) is True
    assert repo.get(bid) is None
    assert repo.delete(bid) is False


def test_search_like(repo: BookRepository) -> None:
    repo.add(_mk("Лев Толстой", "Война и мир", 1869, "роман"))
    repo.add(_mk("Фёдор Достоевский", "Идиот", 1868, "роман"))
    res = repo.search(author="толст")
    assert len(res) == 1
    assert res[0].author.startswith("Лев")


def test_search_year_range(repo: BookRepository) -> None:
    repo.add(_mk(year=1990))
    repo.add(_mk(title="X", year=2005))
    repo.add(_mk(title="Y", year=2015))
    res = repo.search(year_from=2000, year_to=2010)
    assert len(res) == 1
    assert res[0].year == 2005


def test_update(repo: BookRepository) -> None:
    bid = repo.add(_mk())
    b = repo.update(bid, title="New", year=2020)
    assert b.title == "New"
    assert b.year == 2020
    assert repo.get(bid) == b  # type: ignore[arg-type]


def test_stats_by_genre(repo: BookRepository) -> None:
    repo.add(_mk(title="1", genre="роман"))
    repo.add(_mk(title="2", genre="роман"))
    repo.add(_mk(title="3", genre="поэма"))
    stats = dict(repo.stats_by_genre())
    assert stats["роман"] == 2
    assert stats["поэма"] == 1


def test_stats_by_author_and_decade(repo: BookRepository) -> None:
    repo.add(_mk(author="A", title="1", year=1995))
    repo.add(_mk(author="A", title="2", year=1997))
    repo.add(_mk(author="B", title="3", year=2001))
    assert dict(repo.stats_by_author())["A"] == 2
    assert dict(repo.stats_by_decade())["1990-е"] == 2
    assert dict(repo.stats_by_decade())["2000-е"] == 1
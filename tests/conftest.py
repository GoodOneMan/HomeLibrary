"""Общие фикстуры pytest."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.db import init_db
from app.repository import BookRepository


@pytest.fixture()
def repo(tmp_path: Path) -> BookRepository:
    """Репозиторий с чистой БД во временной папке."""
    db = tmp_path / "test.db"
    init_db(db)
    return BookRepository(db)
"""Тесты генерации отчётов."""
from __future__ import annotations

from pathlib import Path

from app.models import Book
from app.repository import BookRepository
from app.reports import generate_html_report, generate_txt_report


def test_txt_report_generated(repo: BookRepository, tmp_path: Path) -> None:
    repo.add(Book("A", "T1", 2000, "роман"))
    repo.add(Book("B", "T2", 2010, "поэма"))
    out = generate_txt_report(repo, tmp_path / "r.txt")
    content = out.read_text(encoding="utf-8")
    assert "ДОМАШНЯЯ БИБЛИОТЕКА" in content
    assert "T1" in content and "T2" in content
    assert "СТАТИСТИКА ПО ЖАНРАМ" in content


def test_html_report_generated(repo: BookRepository, tmp_path: Path) -> None:
    repo.add(Book("A", "T1", 2000, "роман"))
    repo.add(Book("B", "T2", 2010, "поэма"))
    out = generate_html_report(repo, tmp_path / "r.html")
    content = out.read_text(encoding="utf-8")
    assert content.lower().startswith("<!doctype html>")
    assert "T1" in content and "T2" in content
    assert "Краткое резюме" in content


def test_empty_report_does_not_crash(repo: BookRepository, tmp_path: Path) -> None:
    out_txt = generate_txt_report(repo, tmp_path / "empty.txt")
    out_html = generate_html_report(repo, tmp_path / "empty.html")
    assert out_txt.exists() and out_html.exists()
    assert "нет книг" in out_txt.read_text(encoding="utf-8")
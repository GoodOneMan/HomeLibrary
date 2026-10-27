"""Генерация отчётов в TXT и HTML (шаблон подготовлен с помощью LLM)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import Book
from .repository import BookRepository

HTML_TEMPLATE: str = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Отчёт по домашней библиотеке — {generated_at}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f7fa;
          color: #1f2937; margin: 0; padding: 24px; }}
  h1 {{ color: #1d4ed8; }}
  h2 {{ border-bottom: 2px solid #e5e7eb; padding-bottom: 4px; margin-top: 32px; }}
  table {{ border-collapse: collapse; width: 100%; background: #fff;
           box-shadow: 0 1px 4px rgba(0,0,0,.06); border-radius: 8px; overflow: hidden; }}
  th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #eef1f6; }}
  th {{ background: #1d4ed8; color: #fff; }}
  tr:nth-child(even) td {{ background: #f9fafb; }}
  .summary {{ background: #eff6ff; border-left: 4px solid #1d4ed8;
              padding: 12px 16px; border-radius: 6px; }}
  .tag {{ display: inline-block; background: #dbeafe; color: #1e40af;
          padding: 2px 8px; border-radius: 12px; font-size: 12px; }}
</style>
</head>
<body>
<h1>Домашняя библиотека — отчёт</h1>
<p>Сгенерировано: <strong>{generated_at}</strong></p>

<div class="summary">
  <strong>Краткое резюме (автогенерация):</strong>
  <p>{summary}</p>
</div>

<h2>Книги в отчёте ({book_count})</h2>
<table>
  <thead><tr><th>#</th><th>Автор</th><th>Название</th><th>Год</th><th>Жанр</th></tr></thead>
  <tbody>
  {rows}
  </tbody>
</table>

<h2>Статистика по жанрам</h2>
<table><thead><tr><th>Жанр</th><th>Количество</th></tr></thead><tbody>
{genre_rows}
</tbody></table>

<h2>Статистика по авторам</h2>
<table><thead><tr><th>Автор</th><th>Количество</th></tr></thead><tbody>
{author_rows}
</tbody></table>

<h2>Распределение по десятилетиям</h2>
<table><thead><tr><th>Десятилетие</th><th>Количество</th></tr></thead><tbody>
{decade_rows}
</tbody></table>
</body>
</html>
"""


def _build_summary(books: list[Book]) -> str:
    """Простая «ИИ-подобная» текстовая сводка по выборке книг."""
    if not books:
        return "В выборке нет книг."
    genres: dict[str, int] = {}
    for b in books:
        genres[b.genre] = genres.get(b.genre, 0) + 1
    top_genre = max(genres.items(), key=lambda kv: kv[1])
    authors = {b.author for b in books}
    years = [b.year for b in books]
    return (
        f"В выборке {len(books)} книг(и) от {len(authors)} автор(ов). "
        f"Самый популярный жанр — «{top_genre[0]}» ({top_genre[1]} шт.). "
        f"Диапазон годов: {min(years)}–{max(years)}."
    )


def generate_txt_report(
    repo: BookRepository,
    out_path: Path,
    books: list[Book] | None = None,
) -> Path:
    """Формирует текстовый отчёт и сохраняет по указанному пути."""
    books = books if books is not None else repo.list_all()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = [
        "=" * 60,
        "ДОМАШНЯЯ БИБЛИОТЕКА — ОТЧЁТ",
        f"Сгенерировано: {now}",
        "=" * 60,
        "",
        "КРАТКОЕ РЕЗЮМЕ (автогенерация):",
        _build_summary(books),
        "",
        f"КНИГИ В ОТЧЁТЕ ({len(books)}):",
    ]
    for i, b in enumerate(books, 1):
        lines.append(f"  {i:>2}. {b.author} — «{b.title}» ({b.year}, {b.genre})")

    lines += ["", "СТАТИСТИКА ПО ЖАНРАМ:"]
    for g, c in repo.stats_by_genre():
        lines.append(f"  - {g}: {c}")
    lines += ["", "СТАТИСТИКА ПО АВТОРАМ:"]
    for a, c in repo.stats_by_author():
        lines.append(f"  - {a}: {c}")
    lines += ["", "РАСПРЕДЕЛЕНИЕ ПО ДЕСЯТИЛЕТИЯМ:"]
    for d, c in repo.stats_by_decade():
        lines.append(f"  - {d}: {c}")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def generate_html_report(
    repo: BookRepository,
    out_path: Path,
    books: list[Book] | None = None,
) -> Path:
    """Формирует HTML-отчёт и сохраняет по указанному пути."""
    books = books if books is not None else repo.list_all()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = "\n".join(
        f"<tr><td>{i}</td><td>{b.author}</td><td>{b.title}</td>"
        f"<td>{b.year}</td><td><span class='tag'>{b.genre}</span></td></tr>"
        for i, b in enumerate(books, 1)
    )
    genre_rows = "\n".join(
        f"<tr><td>{g}</td><td>{c}</td></tr>" for g, c in repo.stats_by_genre()
    )
    author_rows = "\n".join(
        f"<tr><td>{a}</td><td>{c}</td></tr>" for a, c in repo.stats_by_author()
    )
    decade_rows = "\n".join(
        f"<tr><td>{d}</td><td>{c}</td></tr>" for d, c in repo.stats_by_decade()
    )

    html = HTML_TEMPLATE.format(
        generated_at=now,
        summary=_build_summary(books),
        book_count=len(books),
        rows=rows,
        genre_rows=genre_rows,
        author_rows=author_rows,
        decade_rows=decade_rows,
    )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path
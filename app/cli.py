from __future__ import annotations
import argparse
from pathlib import Path
from .db import init_db
from .models import Book
from .repository import BookRepository
from .reports import generate_html_report, generate_txt_report

REPORTS_DIR: Path = Path(__file__).resolve().parent.parent / "reports_out"


def main() -> None:
    """Точка входа CLI."""
    parser = argparse.ArgumentParser(description="Home Library CLI")
    parser.add_argument(
        "--add",
        nargs=4,
        metavar=("AUTHOR", "TITLE", "YEAR", "GENRE"),
        help="Добавить книгу",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Показать все книги",
    )
    parser.add_argument(
        "--report",
        choices=["txt", "html"],
        help="Сгенерировать отчёт",
    )
    args = parser.parse_args()

    init_db()
    repo = BookRepository()
    REPORTS_DIR.mkdir(exist_ok=True)

    if args.add:
        a, t, y, g = args.add
        try:
            book_id = repo.add(Book(author=a, title=t, year=int(y), genre=g))
            print(f"Добавлена книга id={book_id}")
        except Exception as e:
            print(f"Ошибка: {e}")

    if args.list:
        for b in repo.list_all():
            print(f"[{b.id}] {b.author} — «{b.title}» ({b.year}, {b.genre})")

    if args.report == "txt":
        path = generate_txt_report(repo, REPORTS_DIR / "report.txt")
        print(f"Сохранено: {path}")
    elif args.report == "html":
        path = generate_html_report(repo, REPORTS_DIR / "report.html")
        print(f"Сохранено: {path}")


if __name__ == "__main__":
    main()
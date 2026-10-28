"""Главное окно PySide6."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.db import init_db
from app.models import Book, ValidationError
from app.repository import BookRepository, DuplicateBookError
from app.reports import generate_html_report, generate_txt_report

REPORTS_DIR: Path = Path(__file__).resolve().parent.parent / "reports_out"


class BookEditDialog(QDialog):
    """Диалог редактирования книги (все поля: автор, название, год, жанр)."""

    def __init__(self, book: Book, parent: QWidget | None = None) -> None:
        """Создаёт форму редактирования, предзаполненную данными книги.

        Args:
            book: Исходная книга, поля которой будут показаны в форме.
            parent: Родительский виджет для модальности.
        """
        super().__init__(parent)
        self.setWindowTitle("Редактирование книги")
        self.setMinimumWidth(420)

        # --- Поля формы ---
        self.ed_author = QLineEdit(book.author)
        self.ed_title = QLineEdit(book.title)
        self.sp_year = QSpinBox()
        self.sp_year.setRange(0, 2100)
        self.sp_year.setValue(book.year)
        self.ed_genre = QLineEdit(book.genre)

        # --- Компоновка через QFormLayout: подписи слева, поля справа ---
        form = QFormLayout()
        form.addRow("Автор:", self.ed_author)
        form.addRow("Название:", self.ed_title)
        form.addRow("Год:", self.sp_year)
        form.addRow("Жанр:", self.ed_genre)

        # --- Стандартные кнопки OK/Cancel ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def get_values(self) -> dict[str, object]:
        """Возвращает отредактированные значения в виде словаря.

        Используется после `exec()` == `QDialog.Accepted`.
        """
        return {
            "author": self.ed_author.text().strip(),
            "title": self.ed_title.text().strip(),
            "year": self.sp_year.value(),
            "genre": self.ed_genre.text().strip(),
        }


class MainWindow(QMainWindow):
    """Главное окно «Домашняя библиотека»."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Домашняя библиотека")
        self.resize(1100, 640)
        init_db()
        REPORTS_DIR.mkdir(exist_ok=True)
        self.repo = BookRepository()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # --- Форма добавления ---
        form = QHBoxLayout()
        self.ed_author = QLineEdit()
        self.ed_author.setPlaceholderText("Автор")
        self.ed_title = QLineEdit()
        self.ed_title.setPlaceholderText("Название")
        self.sp_year = QSpinBox()
        self.sp_year.setRange(0, 2100)
        self.sp_year.setValue(2024)
        self.ed_genre = QLineEdit()
        self.ed_genre.setPlaceholderText("Жанр")
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self.on_add)
        for w in (self.ed_author, self.ed_title, self.sp_year, self.ed_genre, btn_add):
            form.addWidget(w)
        root.addLayout(form)

        # --- Поиск и фильтры ---
        search = QHBoxLayout()
        self.ed_search = QLineEdit()
        self.ed_search.setPlaceholderText("Поиск: автор/название/жанр")
        self.sp_from = QSpinBox()
        self.sp_from.setRange(0, 2100)
        self.sp_to = QSpinBox()
        self.sp_to.setRange(0, 2100)
        self.sp_to.setValue(2100)
        self.cmb_order = QComboBox()
        self.cmb_order.addItems(["author", "title", "year", "genre"])
        btn_find = QPushButton("Найти")
        btn_find.clicked.connect(self.refresh)
        for w in (
            self.ed_search,
            QLabel("Год с"),
            self.sp_from,
            QLabel("по"),
            self.sp_to,
            QLabel("Сортировка:"),
            self.cmb_order,
            btn_find,
        ):
            search.addWidget(w)
        root.addLayout(search)

        # --- Таблица ---
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Автор", "Название", "Год", "Жанр"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.on_edit)
        root.addWidget(self.table)

        # --- Кнопки действий ---
        actions = QHBoxLayout()
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self.on_edit)
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self.on_delete)
        btn_txt = QPushButton("Отчёт TXT")
        btn_txt.clicked.connect(lambda: self.on_report("txt"))
        btn_html = QPushButton("Отчёт HTML")
        btn_html.clicked.connect(lambda: self.on_report("html"))
        btn_stats = QPushButton("Статистика")
        btn_stats.clicked.connect(self.on_stats)
        for w in (btn_edit, btn_del, btn_txt, btn_html, btn_stats):
            actions.addWidget(w)
        root.addLayout(actions)

        self.refresh()

    # ---------- helpers ----------
    def _selected_id(self) -> int | None:
        """Возвращает id выбранной в таблице книги или None."""
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def refresh(self) -> None:
        """Обновляет таблицу по текущим фильтрам."""
        text = self.ed_search.text().strip()
        books = self.repo.search(
            author=text or None,
            title=text or None,
            genre=text or None,
            year_from=self.sp_from.value(),
            year_to=self.sp_to.value(),
            order_by=self.cmb_order.currentText(),
        )
        self.table.setRowCount(0)
        for b in books:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, val in enumerate([b.id, b.author, b.title, b.year, b.genre]):
                item = QTableWidgetItem(str(val))
                if c == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c, item)

    # ---------- handlers ----------
    def on_add(self) -> None:
        """Добавляет книгу из полей формы."""
        try:
            book = Book(
                author=self.ed_author.text(),
                title=self.ed_title.text(),
                year=self.sp_year.value(),
                genre=self.ed_genre.text(),
            )
            self.repo.add(book)
            self.refresh()
            self.ed_author.clear()
            self.ed_title.clear()
            self.ed_genre.clear()
        except (ValidationError, DuplicateBookError) as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def on_edit(self) -> None:
        """Редактирует выбранную книгу: автор, название, год, жанр."""
        book_id = self._selected_id()
        if book_id is None:
            return
        book = self.repo.get(book_id)
        if book is None:
            return

        # Открываем диалог со всеми полями, предзаполненными значениями книги.
        dialog = BookEditDialog(book, self)
        if dialog.exec() != QDialog.Accepted:
            return

        values = dialog.get_values()
        try:
            # Пересоздаём Book для валидации новых полей до записи в БД.
            Book(
                author=str(values["author"]),
                title=str(values["title"]),
                year=int(values["year"]),  # type: ignore[arg-type]
                genre=str(values["genre"]),
            )
            # Обновляем все поля одним запросом.
            self.repo.update(book_id, **values)
            self.refresh()
        except ValidationError as e:
            QMessageBox.warning(self, "Ошибка валидации", str(e))
        except DuplicateBookError as e:
            QMessageBox.warning(self, "Дубликат", str(e))
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def on_delete(self) -> None:
        """Удаляет выбранную книгу после подтверждения."""
        book_id = self._selected_id()
        if book_id is None:
            return
        if (
            QMessageBox.question(self, "Удаление", f"Удалить книгу id={book_id}?")
            == QMessageBox.Yes
        ):
            self.repo.delete(book_id)
            self.refresh()

    def on_report(self, kind: str) -> None:
        """Генерирует отчёт TXT или HTML."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = REPORTS_DIR / f"report_{ts}.{kind}"
        try:
            if kind == "txt":
                generate_txt_report(self.repo, out)
            else:
                generate_html_report(self.repo, out)
            QMessageBox.information(self, "Отчёт", f"Сохранено: {out}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def on_stats(self) -> None:
        """Показывает статистику по жанрам."""
        g = ", ".join(f"{genre}: {c}" for genre, c in self.repo.stats_by_genre())
        QMessageBox.information(self, "Статистика по жанрам", g or "Нет данных")
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any


class ValidationError(ValueError):
    """Ошибка валидации полей книги."""


@dataclass(frozen=True)
class Book:
    """Книга домашней библиотеки.

    Атрибуты:
        author: ФИО автора (непустая строка).
        title: Название книги (непустая строка).
        year: Год издания в диапазоне 0..2100.
        genre: Жанр (непустая строка).
        id: Идентификатор в БД (None для новой записи).
    """

    author: str
    title: str
    year: int
    genre: str
    id: int | None = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not isinstance(self.author, str) or not self.author.strip():
            raise ValidationError("Автор не может быть пустым.")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValidationError("Название не может быть пустым.")
        if not isinstance(self.genre, str) or not self.genre.strip():
            raise ValidationError("Жанр не может быть пустым.")
        if not isinstance(self.year, int) or isinstance(self.year, bool):
            raise ValidationError("Год должен быть целым числом.")
        if not (0 <= self.year <= 2100):
            raise ValidationError("Год должен быть в диапазоне 0..2100.")

    def to_dict(self) -> dict[str, Any]:
        """Возвращает книгу как словарь."""
        return asdict(self)

    @classmethod
    def from_row(cls, row: Any) -> "Book":
        """Создаёт книгу из sqlite3.Row или dict."""
        data = dict(row)
        return cls(
            id=data.get("id"),
            author=data["author"],
            title=data["title"],
            year=int(data["year"]),
            genre=data["genre"],
        )
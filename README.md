# Home Library — учёт домашней библиотеки

Приложение на **Python 3.10+** для учёта книг с хранением в **SQLite**
и GUI на **PySide6**. Реализованы CRUD, поиск/фильтрация, статистика
и экспорт отчётов в **TXT** и **HTML**.

## Возможности
- Добавление / редактирование / удаление книг.
- Хранение в `library.db` (таблица `books` + индексы).
- Поиск по автору, названию, жанру (LIKE), фильтр по году (диапазон), сортировка.
- Статистика: по жанрам, авторам, десятилетиям.
- Отчёты: TXT и HTML.
- GUI на PySide6 с QSS-стилями.
- Тесты на pytest.

## Структура
```
home_library/
├── app/        # db.py, models.py, repository.py, reports.py, cli.py
├── ui/         # main_window.py, styles.qss
├── tests/      # pytest-тесты
├── main.py     # запуск GUI
└── requirements.txt
```

## Установка
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск GUI
```bash
python main.py
```

## Тесты
```bash
pytest -q
```

## Отчёты
Сохраняются в `reports_out/` в форматах `.txt` и `.html`.

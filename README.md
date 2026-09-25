# 📚 Library Catalog API

Современный, высокопроизводительный и асинхронный RESTful API для управления каталогом книг, разработанный на **FastAPI**.

Проект демонстрирует production-ready архитектуру: разделение ответственности (Service-Repository pattern), строгую валидацию данных, интеграцию с внешними API с механизмом отказоустойчивости (Graceful Degradation) и полную готовность к развертыванию в Kubernetes.

---

## ✨ Основные возможности

- ⚡ **Асинхронность**: Полная поддержка `async/await` для неблокирующих операций ввода-вывода (БД, внешние API).
- 📖 **Обогащение данных**: Автоматическое получение метаданных (обложка, жанры, издатель, рейтинг) через **Open Library API** при создании книги.
- 🛡️ **Отказоустойчивость**: Если внешний API недоступен, книга все равно будет успешно создана с базовыми данными.
- 🔍 **Продвинутый поиск**: Пагинация и фильтрация по названию, автору, жанру, году и доступности.
- ✅ **Строгая валидация**: Pydantic V2 с кастомными валидаторами (очистка и проверка формата ISBN, контроль года издания).
- 🏥 **Kubernetes**: Эндпоинт `/health` (Liveness) для оркестрации.
- 🏗️ **Чистая архитектура**: Четкое разделение на слои: Routers → Services → Repositories → Database.

---

## 🛠️ Технологический стек

- **Язык**: Python 3.14
- **Фреймворк**: FastAPI
- **База данных**: SQLAlchemy (Async) + PostgreSQL (рекомендуется)
- **Валидация**: Pydantic V2
- **Сервер**: Uvicorn (с поддержкой uvloop)
- **HTTP-клиент**: HTTPX (для асинхронных запросов к Open Library)
- **Миграции**: Alembic
- **Зависимости**: Poetry
- **Запуск async приложения**: Uvicorn

---

## 📂 Структура проекта

```text
Library-Catalog-FastAPI/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │
│   │   │   └── routers/       # Маршруты (endpoints)
│   │   └── dependencies.py    # Внедрение зависимостей (DI)
│   ├── core/
│   │   ├── settings.py          # Настройки приложения (Pydantic Settings)
|   |   ├── exceptions.py        # Исключения
|   |   ├── logging_config.py    # Логгирование
│   │   └── dependency.py        # Настройка Async Engine и Session
│   ├── domain/                # Бизнес-сущности и кастомные исключения
│   ├── external/              # Клиенты внешних API (OpenLibraryClient)
|   ├── models/                # Модели
│   ├── repositories/          # Слой доступа к данным (CRUD операции)
│   ├── services/              # Бизнес-логика (BookService)
|   ├── schemas/               # Pydantic схемы
|   ├── tests/                 # Тестирование и фабрики (pytest)
├   ├── alembic.ini
│   └── main.py                # Точка входа в приложение
├── .env.example               # Пример переменных окружения
├── .gitignore
├── .dockerignore
├── .pre-commit-config.yaml
├── requirements.txt
├── poetry.lock
├── pyproject.toml
├── docker-compose.yaml
└── README.md
```

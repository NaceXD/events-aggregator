# Events Aggregator

Backend-сервис агрегатор для Events Provider API. Кэширует события, предоставляет удобную пагинацию, фильтрацию по датам и управляет регистрацией участников.

## Технологический стек

- **Python 3.14**
- **FastAPI** — веб-фреймворк для API.
- **SQLAlchemy 2.0 (async)** + **asyncpg** — работа с PostgreSQL.
- **Alembic** — миграции базы данных.
- **httpx** — асинхронный HTTP-клиент для запросов к внешнему API.
- **uv** — управление зависимостями и виртуальным окружением.
- **Ruff** — линтер и форматтер (PEP8).
- **pytest** — тестирование.

## Архитектура
Проект следует принципам чистой архитектуры:
- **API (Routers)** — принимают запросы, валидируют данные через Pydantic и вызывают Usecases.
- **Usecases (Бизнес-логика)** — содержат правила (проверка статусов, дедлайнов), не зависят от базы данных и фреймворка.
- **Repositories** — скрывают SQLAlchemy за интерфейсами (Protocols), обеспечивая легкое тестирование.
- **Background Worker** — встроенный воркер (через `lifespan`) для ежедневной синхронизации событий с внешним API.
- **TtlCache** — in-memory кэширование свободных мест на 30 секунд.
## Переменные окружения
```bash
cp .env.example .env
```

## Миграции БД
```bash
uv run alembic upgrade head
```
## Запуск сервера
```bash
uv run uvicorn src.main:app --reload
```

## Тестирование
Запуск линтера и юнит-тестов:
```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest -v
```

## Основные эндпоинты
* `GET /api/health` — проверка работоспособности.

* `POST /api/sync/trigger` — ручной запуск синхронизации с внешним API.

* `GET /api/events` — список событий (пагинация, фильтр по date_from).

* `GET /api/events/{event_id}` — детали события.

* `GET /api/events/{event_id}/seats` — свободные места (с кэшированием).

* `POST /api/tickets` — регистрация на событие.

* `DELETE /api/tickets/{ticket_id}` — отмена регистрации.
# Прогресс

## Текущий этап
Этап 1. Интеграция с Events Provider API (Клиент + Тесты)

## Чеклист по этапам
- [+] Этап 0. Bootstrap
    - [+] uv + ruff + структура
    - [+] health-эндпоинт работает локально
    - [+] Dockerfile и run.sh
    - [+] CI/CD: lint -> build -> deploy

- [+] Этап 1. EventsProviderClient + тесты
    - [+] Настройка `.env` и `config.py`
    - [+] Написание класса `EventsProviderClient`
    - [+] Покрытие клиента тестами (pytest + unittest.mock)

- [ ] Этап 2. EventsPaginator + тесты
- [ ] Этап 3. БД + репозитории + миграции
- [ ] Этап 4. Синхронизация + trigger + воркер
- [ ] Этап 5. Events endpoints
- [ ] Этап 6. Tickets endpoints
- [ ] Этап 7. Полировка

## Открытые вопросы
- ...

## Заметки
- Выбран стек: FastAPI + uv + ruff + httpx (async).
- В `run.sh` используется флаг `uv run --no-sync`. Без этого Kubenetes не запускается так как нет доступа в интеренет и `uv` не может проверить/скачать зависимости при старте
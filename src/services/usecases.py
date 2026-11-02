import logging
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import TicketCreate
from src.repositories import (
    SqlAlchemyEventRepository,
    SqlAlchemyPlaceRepository,
    SqlAlchemySyncStateRepository,
    SqlAlchemyTicketRepository,
)
from src.repositories.protocols import (
    EventRepository,
    PlaceRepository,
    SyncStateRepository,
    TicketRepository,
)
from src.services import EventsPaginator, EventsProviderClient
from src.services.cache import TtlCache
from src.services.exceptions import (
    EventNotFoundError,
    EventNotPublishedError,
    RegistrationDeadlinePassedError,
    TicketNotFoundError,
)

logger = logging.getLogger(__name__)
seats_cache = TtlCache()


def parse_date_fields(data: dict, fields: list[str]) -> None:
    """
    Вспомогательная функция:
    Конвектирует строковые поля с датами из ответа API в объекты
    datetime, так как asyncpg требует строгой типизации при вставке в БД
    """
    for field in fields:
        data[field] = datetime.fromisoformat(data[field])


def build_page_url(base_url: str, page: int) -> str:
    """
    Вспомогательная функция:
    Формирует URL для пагинации (next/previous), изменяя номер
    страницы в исходном запросе клиента.
    """
    parsed = urlparse(base_url)
    params = parse_qs(parsed.query)
    params["page"] = [str(page)]
    new_query = urlencode(params, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


class SyncUsecase:
    """
    Инкрементальная синхронизация событий и площадок с внешним API.
    Обновляет синхронизации в БД.
    """

    def __init__(
        self,
        client: EventsProviderClient,
        places: PlaceRepository,
        events: EventRepository,
        sync_state: SyncStateRepository,
    ):
        self.client = client
        self.places = places
        self.events = events
        self.sync_state = sync_state

    async def do(self):
        state = await self.sync_state.get()
        if state:
            changed_at = state.last_changed_at.date().isoformat()
            max_changed_at: datetime | None = state.last_changed_at
        else:
            changed_at = "2000-01-01"
            max_changed_at = None
        logger.info("Синхронизация начата. Дата изменений: %s", changed_at)
        paginator = EventsPaginator(client=self.client, changed_at=changed_at)
        place_date_fields = ["changed_at", "created_at"]
        event_date_fields = [
            "event_time",
            "registration_deadline",
            "changed_at",
            "created_at",
            "status_changed_at",
        ]
        async for event_data in paginator:
            place_data = event_data.pop("place")
            parse_date_fields(place_data, place_date_fields)
            parse_date_fields(event_data, event_date_fields)
            await self.places.upsert(place_data=place_data)
            event_data["place_id"] = place_data["id"]
            await self.events.upsert(event_data=event_data)
            event_changed_at = event_data["changed_at"]
            if max_changed_at is None or event_changed_at > max_changed_at:
                max_changed_at = event_changed_at
        logger.info("Синхронизация завершена. Последняя дата: %s", max_changed_at)
        await self.sync_state.update(
            {
                "last_sync_time": datetime.now(UTC),
                "last_changed_at": max_changed_at or datetime.now(UTC),
                "sync_status": "success",
            }
        )
        logger.info("Состояние синхронизации сохранено.")


def create_sync_usecase(db: AsyncSession) -> SyncUsecase:
    places_repo = SqlAlchemyPlaceRepository(session=db)
    events_repo = SqlAlchemyEventRepository(session=db)
    sync_state_repo = SqlAlchemySyncStateRepository(session=db)
    client = EventsProviderClient()
    return SyncUsecase(
        client=client,
        places=places_repo,
        events=events_repo,
        sync_state=sync_state_repo,
    )


class ListEventsUsecase:
    """
    Возвращает постраничный список событий с фильтрацией по дате
    и формированием ссылок пагинации.
    """

    def __init__(self, events: EventRepository):
        self.events = events

    async def do(self, date_from: str | None, page: int, page_size: int, base_url: str) -> dict:
        count = await self.events.count(date_from=date_from)
        results = await self.events.list(date_from=date_from, page=page, page_size=page_size)
        if page * page_size >= count:
            next_url = None
        else:
            next_url = build_page_url(base_url, page + 1)

        if page <= 1:
            prev_url = None
        else:
            prev_url = build_page_url(base_url, page - 1)

        return {"count": count, "next": next_url, "previous": prev_url, "results": results}


def create_list_events_usecase(db: AsyncSession) -> ListEventsUsecase:
    events_repo = SqlAlchemyEventRepository(session=db)
    return ListEventsUsecase(events=events_repo)


class GetEventUsecase:
    """
    Возращает детали события по ID.
    Бросает EventNotFoundError, если события нет.
    """

    def __init__(self, events: EventRepository):
        self.events = events

    async def do(self, event_id: str):
        event = await self.events.get(event_id=event_id)
        if event is None:
            raise EventNotFoundError

        return event


def create_get_event_usecase(db: AsyncSession) -> GetEventUsecase:
    events_repo = SqlAlchemyEventRepository(session=db)
    return GetEventUsecase(events=events_repo)


class GetEventSeatsUsecase:
    """
    Возвращает свободные места. Кэширует результат на 30сек.
    Проверяет статус перед запросом к API.
    """

    def __init__(self, events: EventRepository, client: EventsProviderClient, cache: TtlCache):
        self.events = events
        self.client = client
        self.cache = cache

    async def do(self, event_id: str):
        event = await self.events.get(event_id=event_id)
        if not event:
            raise EventNotFoundError

        if event.status != "published":
            raise EventNotPublishedError

        cached_seats = self.cache.get(event_id)
        if cached_seats is not None:
            return {"event_id": event_id, "available_seats": cached_seats}

        data = await self.client.get_seats(event_id)
        self.cache.set(event_id, data["seats"])
        return {"event_id": event_id, "available_seats": data["seats"]}


def create_get_event_seats_usecase(db: AsyncSession) -> GetEventSeatsUsecase:
    events_repo = SqlAlchemyEventRepository(session=db)
    client = EventsProviderClient()
    return GetEventSeatsUsecase(events=events_repo, client=client, cache=seats_cache)


class CreateTicketUsecase:
    """
    Регистрирует участника. Проверяет статус события и дедлайн,
    делает запрос во внешний API и сохраняет билет в БД.
    """

    def __init__(
        self, events: EventRepository, tickets: TicketRepository, client: EventsProviderClient
    ):
        self.events = events
        self.tickets = tickets
        self.client = client

    async def do(self, request: TicketCreate) -> dict:
        event = await self.events.get(event_id=(str(request.event_id)))
        if event is None:
            raise EventNotFoundError
        if event.status != "published":
            raise EventNotPublishedError
        if datetime.now(UTC) > event.registration_deadline:
            raise RegistrationDeadlinePassedError

        response = await self.client.register(
            event_id=str(request.event_id),
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            seat=request.seat,
        )
        await self.tickets.create(
            {
                "ticket_id": response["ticket_id"],
                "event_id": request.event_id,
                "first_name": request.first_name,
                "last_name": request.last_name,
                "email": request.email,
                "seat": request.seat,
                "created_at": datetime.now(UTC),
            }
        )
        return {"ticket_id": response["ticket_id"]}


def create_ticket_usecase(db: AsyncSession) -> CreateTicketUsecase:
    event_repo = SqlAlchemyEventRepository(session=db)
    ticket_repo = SqlAlchemyTicketRepository(session=db)
    client = EventsProviderClient()
    return CreateTicketUsecase(events=event_repo, tickets=ticket_repo, client=client)


class CancelTicketUsecase:
    """
    Отменяет регистрацию. Удаляет билет из БД и вызывает отмену во внешнем API.
    """

    def __init__(self, tickets: TicketRepository, client: EventsProviderClient):
        self.tickets = tickets
        self.client = client

    async def do(self, ticket_id: str) -> dict:
        ticket = await self.tickets.get_by_ticket_id(ticket_id=ticket_id)
        if ticket is None:
            raise TicketNotFoundError
        await self.client.unregister(event_id=str(ticket.event_id), ticket_id=ticket_id)
        await self.tickets.delete(ticket_id=ticket_id)
        return {"success": True}


def cancel_ticket_usecase(db: AsyncSession) -> CancelTicketUsecase:
    ticket_repo = SqlAlchemyTicketRepository(session=db)
    client = EventsProviderClient()
    return CancelTicketUsecase(tickets=ticket_repo, client=client)

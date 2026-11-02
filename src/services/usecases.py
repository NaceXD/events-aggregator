import logging
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import (
    SqlAlchemyEventRepository,
    SqlAlchemyPlaceRepository,
    SqlAlchemySyncStateRepository,
)
from src.repositories.protocols import EventRepository, PlaceRepository, SyncStateRepository
from src.services import EventsPaginator, EventsProviderClient

logger = logging.getLogger(__name__)


def parse_date_fields(data: dict, fields: list[str]) -> None:
    for field in fields:
        data[field] = datetime.fromisoformat(data[field])


def build_page_url(base_url: str, page: int) -> str:
    parsed = urlparse(base_url)
    params = parse_qs(parsed.query)
    params["page"] = [str(page)]
    new_query = urlencode(params, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


class SyncUsecase:
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

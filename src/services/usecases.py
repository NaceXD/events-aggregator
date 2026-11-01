import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import (
    SqlAlchemyEventRepository,
    SqlAlchemyPlaceRepository,
    SqlAlchemySyncStateRepository,
)
from src.repositories.protocols import EventRepository, PlaceRepository, SyncStateRepository
from src.services import EventsPaginator, EventsProviderClient

logger = logging.getLogger(__name__)


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

        async for event_data in paginator:
            place_data = event_data.pop("place")
            await self.places.upsert(place_data=place_data)
            event_data["place_id"] = place_data["id"]
            await self.events.upsert(event_data=event_data)
            event_changed_at = datetime.fromisoformat(event_data["changed_at"])
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

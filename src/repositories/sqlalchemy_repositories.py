from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import Event, Place, SyncState, Ticket


class SqlAlchemyPlaceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, place_id: str) -> Place | None:
        query = select(Place).where(Place.id == place_id)
        results = await self.session.execute(query)
        return results.scalar_one_or_none()

    async def upsert(self, place_data: dict) -> None:
        await self.session.merge(Place(**place_data))
        await self.session.commit()


class SqlAlchemyEventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, event_id: str) -> Event | None:
        query = select(Event).where(Event.id == event_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def upsert(self, event_data: dict) -> None:
        await self.session.merge(Event(**event_data))
        await self.session.commit()

    async def list(self, date_from: str | None, page: int, page_size: int) -> Sequence[Event]:
        query = select(Event)
        if date_from is not None:
            query = query.where(Event.event_time >= date_from)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(query)
        return result.scalars().all()


class SqlAlchemyTicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, ticket_data: dict) -> Ticket:
        ticket = Ticket(**ticket_data)
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def get_by_ticket_id(self, ticket_id: str) -> Ticket | None:
        query = select(Ticket).where(Ticket.ticket_id == ticket_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class SqlAlchemySyncStateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self) -> SyncState | None:
        query = select(SyncState).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, state_data: dict) -> None:
        state = await self.get()
        if state:
            for key, value in state_data.items():
                setattr(state, key, value)
        else:
            state = SyncState(id=1, **state_data)
            self.session.add(state)

        await self.session.commit()

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import EventDetail, EventsListResponse
from src.db.session import get_db
from src.services import create_get_event_usecase, create_list_events_usecase
from src.services.exceptions import EventNotFoundError

router = APIRouter()


@router.get("/events", response_model=EventsListResponse)
async def list_events(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    usecase = create_list_events_usecase(db=db)

    base_url = str(request.url)

    return await usecase.do(date_from=date_from, page=page, page_size=page_size, base_url=base_url)


@router.get("/events/{event_id}", response_model=EventDetail)
async def get_event(event_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    usecase = create_get_event_usecase(db=db)

    try:
        result = await usecase.do(event_id=str(event_id))
    except EventNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено"
        ) from e
    return result

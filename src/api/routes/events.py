from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import EventsListResponse
from src.db.session import get_db
from src.services import create_list_events_usecase

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

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import TicketCreate, TicketResponse
from src.db.session import get_db
from src.services import cancel_ticket_usecase, create_ticket_usecase
from src.services.exceptions import (
    EventNotFoundError,
    EventNotPublishedError,
    RegistrationDeadlinePassedError,
    TicketNotFoundError,
)

router = APIRouter()


@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request: TicketCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    usecase = create_ticket_usecase(db=db)
    try:
        return await usecase.do(request=request)
    except EventNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено"
        ) from e
    except EventNotPublishedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Событие не опубликовано"
        ) from e
    except RegistrationDeadlinePassedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Дедлайн регистрации прошел"
        ) from e


@router.delete("/tickets/{ticket_id}")
async def cancel_ticket(ticket_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    usecase = cancel_ticket_usecase(db=db)
    try:
        return await usecase.do(ticket_id=ticket_id)
    except TicketNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Билет не найден") from e

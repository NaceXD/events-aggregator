import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.services import create_sync_usecase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/sync/trigger")
async def trigger_sync(db: Annotated[AsyncSession, Depends(get_db)]):
    usecase = create_sync_usecase(db=db)
    try:
        await usecase.do()
    except Exception as e:
        logger.error("Ошибка синхронизации %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ошибка синхронизации",
        ) from e
    return {"status": "success"}

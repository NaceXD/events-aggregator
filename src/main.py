import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.routes import router
from src.db.session import AsyncSessionLocal
from src.services import EventsProviderClient, create_sync_usecase
from src.services.exceptions import ProviderError

logger = logging.getLogger(__name__)


async def periodic_sync():
    while True:
        logger.info("Запуск фоновой синхронизации ...")
        try:
            async with AsyncSessionLocal() as db:
                usecase = create_sync_usecase(db=db)
                await usecase.do()
            logger.info("Фоновая синхронизация завершена успешно.")
        except Exception as e:
            logger.error("Ошибка фоновой синхронизации: %s", e)
        await asyncio.sleep(24 * 60 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.events_client = EventsProviderClient()
    sync_task = asyncio.create_task(periodic_sync())

    yield

    sync_task.cancel()
    await app.state.events_client.close()


app = FastAPI(title="Events Aggregator", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Ошибка валидации данных: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Ошибка валидации данных", "errors": exc.errors()},
    )


@app.exception_handler(ProviderError)
async def provider_error_handler(request: Request, exc: ProviderError):
    logger.error("Ошибка провайдера: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Ошибка при обращении к внешнему сервису. Попробуйте позже."},
    )


app.include_router(router, prefix="/api")

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.db.session import AsyncSessionLocal
from src.services import EventsProviderClient, create_sync_usecase

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

app.include_router(router, prefix="/api")

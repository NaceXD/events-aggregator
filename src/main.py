from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.services import EventsProviderClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.events_client = EventsProviderClient()
    yield
    await app.state.events_client.close()


app = FastAPI(title="Events Aggregator", lifespan=lifespan)

app.include_router(router, prefix="/api")

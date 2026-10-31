from fastapi import FastAPI

from src.api.routes import router

app = FastAPI(title="Events Aggregator")

app.include_router(router, prefix="/api")

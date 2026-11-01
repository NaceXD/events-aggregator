from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import settings

raw_url = settings.postgres_connection_string.get_secret_value()
db_url = raw_url.replace("postgres://", "postgresql+asyncpg://").replace(
    "postgresql://", "postgresql+asyncpg://"
)

engine = create_async_engine(db_url)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

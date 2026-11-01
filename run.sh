uv run -no-sync alembic upgrade head
uv run --no-sync uvicorn src.main:app --host 0.0.0.0 --port 8000

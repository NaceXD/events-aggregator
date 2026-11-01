from unittest.mock import AsyncMock, Mock

import pytest

from src.services import EventsProviderClient


@pytest.fixture
def client():
    client = EventsProviderClient()
    client.client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_get_events(client):
    mock_response = Mock()
    mock_response.json.return_value = {"result": [], "next": None}
    client.client.get.return_value = mock_response

    result = await client.get_events(changed_at="2026-01-01")

    assert result == {"result": [], "next": None}
    client.client.get.assert_called_once_with(
        f"{client.base_url}/api/events/?changed_at=2026-01-01"
    )


@pytest.mark.asyncio
async def test_get_seats(client):
    mock_response = Mock()
    mock_response.json.return_value = {"seats": ["A1", "A4", "B2", "B15", "C3"]}
    client.client.get.return_value = mock_response

    result = await client.get_seats(event_id="550e8400-e29b-41d4-a716-446655440000")

    assert result == {"seats": ["A1", "A4", "B2", "B15", "C3"]}
    client.client.get.assert_called_once_with(
        f"{client.base_url}/api/events/550e8400-e29b-41d4-a716-446655440000/seats/"
    )


@pytest.mark.asyncio
async def test_register(client):
    mock_response = Mock()
    mock_response.json.return_value = {"ticket_id": "1fed0122-b675-42e2-8ae7-49bfb53e8d7f"}
    client.client.post.return_value = mock_response

    event_id = "550e8400-e29b-41d4-a716-446655440000"
    payload = {"first_name": "Иван", "last_name": "Иванов", "email": "user@test.com", "seat": "A1"}

    result = await client.register(
        event_id=event_id,
        **payload,
    )

    assert result == {"ticket_id": "1fed0122-b675-42e2-8ae7-49bfb53e8d7f"}

    client.client.post.assert_called_once_with(
        url=f"{client.base_url}/api/events/{event_id}/register/",
        json=payload,
    )


@pytest.mark.asyncio
async def test_unregister(client):
    mock_response = Mock()
    mock_response.json.return_value = {"success": True}
    client.client.request.return_value = mock_response

    event_id = "550e8400-e29b-41d4-a716-446655440000"
    payload = {"ticket_id": "1fed0122-b675-42e2-8ae7-49bfb53e8d7f"}

    result = await client.unregister(
        event_id=event_id,
        **payload,
    )

    assert result == {"success": True}

    client.client.request.assert_called_once_with(
        "DELETE", url=f"{client.base_url}/api/events/{event_id}/unregister/", json=payload
    )

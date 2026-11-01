from unittest.mock import AsyncMock

import pytest

from src.services import EventsPaginator


@pytest.mark.asyncio
async def test_paginator():
    mock_client = AsyncMock()

    page_1 = {"results": [{"id": "1"}, {"id": "2"}], "next": "http://api/?cursor=abc"}
    page_2 = {"results": [{"id": "3"}], "next": None}

    mock_client.get_events.side_effect = [page_1, page_2]

    paginator = EventsPaginator(client=mock_client)
    all_events = []
    async for event in paginator:
        all_events.append(event)

    assert len(all_events) == 3
    assert all_events == [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    assert mock_client.get_events.call_count == 2

    mock_client.get_events.assert_called_with("2000-01-01", "abc")


@pytest.mark.asyncio
async def test_paginator_skips_empty_page():
    mock_client = AsyncMock()
    page_1 = {"results": [], "next": "http://api/?cursor=test"}
    page_2 = {"results": [{"id": "1"}], "next": None}

    mock_client.get_events.side_effect = [page_1, page_2]
    paginator = EventsPaginator(client=mock_client)

    all_events = []
    async for event in paginator:
        all_events.append(event)

    assert len(all_events) == 1
    assert mock_client.get_events.call_count == 2

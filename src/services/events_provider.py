import httpx

from src.core.config import settings
from src.services.exceptions import ProviderError


class EventsProviderClient:
    def __init__(self):
        self.base_url = settings.events_provider_url
        self.headers = {"x-api-key": settings.events_provider_api_key.get_secret_value()}
        self.client = httpx.AsyncClient(headers=self.headers)

    async def get_events(self, changed_at: str, cursor: str | None = None) -> dict:
        url = f"{self.base_url}/api/events/"
        params = {"changed_at": changed_at}
        if cursor:
            params["cursor"] = cursor
        try:
            response = await self.client.get(url=url, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"Ошибка провайдера: {e.response.status_code}") from e

        return response.json()

    async def get_seats(self, event_id: str) -> dict:
        url = f"{self.base_url}/api/events/{event_id}/seats/"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"Ошибка провайдера: {e.response.status_code}") from e

        return response.json()

    async def register(
        self, event_id: str, first_name: str, last_name: str, email: str, seat: str
    ) -> dict:
        url = f"{self.base_url}/api/events/{event_id}/register/"
        payload = {"first_name": first_name, "last_name": last_name, "email": email, "seat": seat}
        try:
            response = await self.client.post(url=url, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"Ошибка провайдера: {e.response.status_code}") from e

        return response.json()

    async def unregister(self, event_id: str, ticket_id: str) -> dict:
        url = f"{self.base_url}/api/events/{event_id}/unregister/"
        payload = {"ticket_id": ticket_id}
        try:
            response = await self.client.request("DELETE", url=url, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ProviderError(f"Ошибка провайдера: {e.response.status_code}") from e

        return response.json()

    async def close(self):
        await self.client.aclose()

import httpx

from src.core.config import settings


class EventsProviderClient:
    def __init__(self):
        self.base_url = settings.events_provider_url
        self.headers = {"x-api-key": settings.events_provider_api_key.get_secret_value()}
        self.client = httpx.AsyncClient(headers=self.headers)

    async def get_events(self, changed_at: str, cursor: str | None = None) -> dict:
        url = f"{self.base_url}/api/events/?changed_at={changed_at}"
        if cursor:
            url += f"&cursor={cursor}"
        response = await self.client.get(url)
        return response.json()

    async def get_seats(self, event_id: str) -> dict:
        url = f"{self.base_url}/api/events/{event_id}/seats/"
        response = await self.client.get(url)
        return response.json()

    async def register(
        self, event_id: str, first_name: str, last_name: str, email: str, seat: str
    ) -> dict:
        url = f"{self.base_url}/api/events/{event_id}/register/"
        payload = {"first_name": first_name, "last_name": last_name, "email": email, "seat": seat}
        response = await self.client.post(url=url, json=payload)
        return response.json()

    async def unregister(self, event_id: str, ticket_id: str) -> dict:
        url = f"{self.base_url}/api/events/{event_id}/unregister/"
        payload = {"ticket_id": ticket_id}
        response = await self.client.request("DELETE", url=url, json=payload)
        return response.json()

    async def close(self):
        await self.client.aclose()

import urllib.parse

from src.services import EventsProviderClient


def extract_cursor(next_url: str | None) -> str | None:
    if next_url is None:
        return None
    query = urllib.parse.urlparse(next_url).query
    result = urllib.parse.parse_qs(query)
    return result.get("cursor", [None])[0]


class EventsPaginator:
    def __init__(self, client: EventsProviderClient, changed_at: str = "2000-01-01"):
        self.client = client
        self.changed_at = changed_at

        self.cursor = None
        self.results = []
        self.index = 0
        self.has_more = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.results):
            if not self.has_more:
                raise StopAsyncIteration
            response = await self.client.get_events(self.changed_at, self.cursor)

            self.results = response["results"]
            self.index = 0
            self.cursor = extract_cursor(response["next"])
            self.has_more = response["next"] is not None

            if not self.results:
                return await self.__anext__()
        event = self.results[self.index]
        self.index += 1
        return event

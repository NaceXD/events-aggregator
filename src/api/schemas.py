import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlaceOut(BaseModel):
    id: uuid.UUID
    name: str
    city: str
    address: str

    model_config = ConfigDict(from_attributes=True)


class PlaceDetail(PlaceOut):
    seats_pattern: str


class EventOut(BaseModel):
    id: uuid.UUID
    name: str
    place: PlaceOut
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int

    model_config = ConfigDict(from_attributes=True)


class EventDetail(EventOut):
    place: PlaceDetail


class EventsListResponse(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventOut]

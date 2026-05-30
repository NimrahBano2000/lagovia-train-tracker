from pydantic import BaseModel
from Departure import Departure

class DeparturesResponse(BaseModel):
    query: str
    matched_stations: list[str]
    window_minutes: int
    generated_at_utc: str
    departures: list[Departure]
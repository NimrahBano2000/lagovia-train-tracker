from pydantic import BaseModel, Field
from typing import Optional

class Departure(BaseModel):
    train_number: str = Field(..., description="Friendly train ID, e.g. 'IC 1234'")
    destination: str = Field(..., description="Terminus station name")
    station: str = Field(..., description="Departure station name")
    scheduled_time_utc: str = Field(..., description="ISO 8601 UTC timestamp")
    scheduled_time_local: str = Field(..., description="HH:MM in Europe/Brussels")
    delay_minutes: int = Field(..., description="Lateness in minutes; 0 = on time")
    platform: Optional[str] = Field(None, description="Platform if announced")
    canceled: bool = Field(False, description="True if canceled")
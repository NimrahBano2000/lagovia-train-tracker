from pydantic import BaseModel
from typing import Optional

class ErrorBody(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None
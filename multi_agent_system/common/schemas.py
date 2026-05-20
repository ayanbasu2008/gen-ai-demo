from pydantic import BaseModel

class Request(BaseModel):
    id: str
    source: str
    content: str
    timestamp: str

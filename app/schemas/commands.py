from pydantic import BaseModel, Field
from typing import Optional


class CreateThreadRequest(BaseModel):
    thread_id: Optional[str] = Field(
        None, description="Optional client-provided thread id"
    )


class CreateThreadResponse(BaseModel):
    thread_id: str
    event_id: str


class SendMessageRequest(BaseModel):
    thread_id: str
    content: str = Field(..., min_length=1)


class SendMessageResponse(BaseModel):
    thread_id: str
    event_id: str


class ForkThreadRequest(BaseModel):
    source_thread_id: str
    event_number: int


class ForkThreadResponse(BaseModel):
    new_thread_id: str

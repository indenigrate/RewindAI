import uuid
from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from app.core.event_store import EventStore
from app.schemas.commands import (
    CreateThreadRequest,
    CreateThreadResponse,
    SendMessageRequest,
    SendMessageResponse,
    ForkThreadRequest,
    ForkThreadResponse,
)
from app.db.fastapi import get_db


router = APIRouter(prefix="/commands", tags=["commands"])


def get_event_store(conn: Connection = Depends(get_db)) -> EventStore:
    return EventStore(conn)

@router.post("/create-thread", response_model=CreateThreadResponse)
def create_thread(
    req: CreateThreadRequest,
    store: EventStore = Depends(get_event_store),
):
    thread_id = req.thread_id or f"thread-{uuid.uuid4().hex[:8]}"

    event = store.append_event(
        thread_id=thread_id,
        event_type="ThreadCreated",
        payload={"thread_id": thread_id},
    )

    return CreateThreadResponse(
        thread_id=thread_id,
        event_id=str(event.event_id),
    )

@router.post("/send-message", response_model=SendMessageResponse)
def send_message(
    req: SendMessageRequest,
    store: EventStore = Depends(get_event_store),
):
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    event = store.append_event(
        thread_id=req.thread_id,
        event_type="UserMessageAdded",
        payload={
            "content": req.content,
            "role": "user",
        },
    )

    return SendMessageResponse(
        thread_id=req.thread_id,
        event_id=str(event.event_id),
    )


@router.post("/fork-thread", response_model=ForkThreadResponse)
def fork_thread(
    req: ForkThreadRequest,
    store: EventStore = Depends(get_event_store),
):
    new_thread_id = f"branch-{uuid.uuid4().hex[:8]}"

    store.append_events(
        thread_id=new_thread_id,
        events=[
            (
                "ThreadCreated",
                {"thread_id": new_thread_id},
            ),
            (
                "ThreadForked",
                {
                    "parent_thread_id": req.source_thread_id,
                    "from_event_number": req.event_number,
                },
            ),
        ],
    )

    return ForkThreadResponse(new_thread_id=new_thread_id)

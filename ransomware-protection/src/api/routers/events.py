from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field

from src.core.database import get_db_dependency
from src.api.models.database import SecurityEvent

router = APIRouter()


class EventCreate(BaseModel):
    host_id: int
    event_type: str = Field(..., description="Type of security event")
    event_source: Optional[str] = None
    severity: str = "info"
    process_name: Optional[str] = None
    process_path: Optional[str] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    user: Optional[str] = None
    action: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    raw_data: Optional[dict] = None


class EventResponse(BaseModel):
    id: int
    host_id: int
    event_type: str
    severity: str
    process_name: Optional[str]
    file_path: Optional[str]
    user: Optional[str]
    ai_risk_score: Optional[float]
    timestamp: datetime


class EventBatchCreate(BaseModel):
    events: List[EventCreate]


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event_data: EventCreate, db=Depends(get_db_dependency())):
    event = SecurityEvent(**event_data.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def create_events_batch(batch_data: EventBatchCreate, db=Depends(get_db_dependency())):
    events = []
    for event_data in batch_data.events:
        event = SecurityEvent(**event_data.model_dump())
        events.append(event)
        db.add(event)

    await db.commit()
    for event in events:
        await db.refresh(event)

    return {"message": f"Created {len(events)} events", "event_ids": [e.id for e in events]}


@router.get("/", response_model=List[EventResponse])
async def get_events(
    host_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    min_risk_score: Optional[float] = Query(None, ge=0, le=1),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db=Depends(get_db_dependency()),
):
    events = await query_events(db, host_id, event_type, severity, min_risk_score, limit, offset)
    return events


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db=Depends(get_db_dependency())):
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.get("/statistics/overview")
async def get_event_statistics(
    host_id: Optional[int] = Query(None),
    hours: int = Query(24, ge=1, le=168),
    db=Depends(get_db_dependency()),
):
    stats = await get_event_stats(db, host_id, hours)
    return stats


async def query_events(db, host_id, event_type, severity, min_risk_score, limit, offset):
    pass


async def get_event_by_id(db, event_id):
    pass


async def get_event_stats(db, host_id, hours):
    pass

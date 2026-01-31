from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field

from src.core.database import get_db_dependency
from src.api.models.database import Alert, AlertStatus, ThreatLevel

router = APIRouter()


class AlertCreate(BaseModel):
    title: str
    description: Optional[str] = None
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    host_id: Optional[int] = None
    detection_type: Optional[str] = None
    attack_vector: Optional[str] = None
    risk_score: float = 0.0
    confidence_score: float = 0.0


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    threat_level: Optional[ThreatLevel] = None
    assigned_to: Optional[int] = None
    false_positive: Optional[bool] = None


class AlertResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    threat_level: str
    status: str
    risk_score: float
    confidence_score: float
    host_id: Optional[int]
    created_at: datetime
    updated_at: datetime


class AlertDetailResponse(AlertResponse):
    detection_type: Optional[str]
    attack_vector: Optional[str]
    recommended_actions: Optional[List[str]]
    affected_systems: Optional[List[str]]
    timeline: Optional[List[dict]]


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    status_filter: Optional[AlertStatus] = Query(None, alias="status"),
    threat_level: Optional[ThreatLevel] = Query(None),
    host_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db=Depends(get_db_dependency()),
):
    query = AlertFilter(status=status_filter, threat_level=threat_level, host_id=host_id)
    alerts = await query_alerts(db, query, limit, offset)
    return alerts


@router.get("/{alert_id}", response_model=AlertDetailResponse)
async def get_alert(alert_id: int, db=Depends(get_db_dependency())):
    alert = await get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(alert_id: int, update_data: AlertUpdate, db=Depends(get_db_dependency())):
    alert = await get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    update_data_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_data_dict.items():
        setattr(alert, field, value)

    if update_data.status == AlertStatus.RESOLVED:
        alert.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)
    return alert


@router.post("/{alert_id}/timeline", status_code=status.HTTP_201_CREATED)
async def add_timeline_entry(
    alert_id: int,
    action: str,
    actor: Optional[str] = None,
    details: Optional[dict] = None,
    db=Depends(get_db_dependency()),
):
    alert = await get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    timeline_entry = AlertTimeline(
        alert_id=alert_id, action=action, actor=actor, details=details, timestamp=datetime.utcnow()
    )
    db.add(timeline_entry)
    await db.commit()

    return {"message": "Timeline entry added"}


@router.get("/statistics/summary")
async def get_alert_statistics(db=Depends(get_db_dependency())):
    stats = await get_alert_stats(db)
    return stats


async def query_alerts(db, query, limit, offset):
    pass


async def get_alert_by_id(db, alert_id):
    pass


async def get_alert_stats(db):
    pass


class AlertTimeline(BaseModel):
    pass


class AlertFilter:
    def __init__(self, status=None, threat_level=None, host_id=None):
        self.status = status
        self.threat_level = threat_level
        self.host_id = host_id

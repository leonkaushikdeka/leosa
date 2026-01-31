from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel

from src.core.database import get_db_dependency
from src.api.models.database import Host, HostStatus

router = APIRouter()


class HostCreate(BaseModel):
    hostname: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    cloud_provider: Optional[str] = None
    cloud_instance_id: Optional[str] = None
    metadata: Optional[dict] = None


class HostUpdate(BaseModel):
    ip_address: Optional[str] = None
    status: Optional[HostStatus] = None
    os_version: Optional[str] = None
    agent_version: Optional[str] = None
    metadata: Optional[dict] = None


class HostResponse(BaseModel):
    id: int
    hostname: str
    ip_address: Optional[str]
    status: str
    os_type: Optional[str]
    cloud_provider: Optional[str]
    last_seen: datetime
    created_at: datetime


class HostDetailResponse(HostResponse):
    mac_address: Optional[str]
    os_version: Optional[str]
    cloud_instance_id: Optional[str]
    agent_version: Optional[str]
    metadata: Optional[dict]


@router.get("/", response_model=List[HostResponse])
async def get_hosts(
    status_filter: Optional[HostStatus] = Query(None),
    cloud_provider: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db=Depends(get_db_dependency()),
):
    hosts = await query_hosts(db, status_filter, cloud_provider, limit, offset)
    return hosts


@router.get("/{host_id}", response_model=HostDetailResponse)
async def get_host(host_id: int, db=Depends(get_db_dependency())):
    host = await get_host_by_id(db, host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    return host


@router.put("/{host_id}", response_model=HostResponse)
async def update_host(host_id: int, update_data: HostUpdate, db=Depends(get_db_dependency())):
    host = await get_host_by_id(db, host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    update_data_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_data_dict.items():
        setattr(host, field, value)

    host.last_seen = datetime.utcnow()
    await db.commit()
    await db.refresh(host)
    return host


@router.post("/{host_id}/quarantine")
async def quarantine_host(host_id: int, db=Depends(get_db_dependency())):
    host = await get_host_by_id(db, host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    host.status = HostStatus.QUARANTINED
    await db.commit()

    return {"message": f"Host {host.hostname} quarantined successfully"}


@router.post("/{host_id}/release")
async def release_host(host_id: int, db=Depends(get_db_dependency())):
    host = await get_host_by_id(db, host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    host.status = HostStatus.ONLINE
    await db.commit()

    return {"message": f"Host {host.hostname} released from quarantine"}


@router.get("/{host_id}/events")
async def get_host_events(
    host_id: int, limit: int = Query(50, ge=1, le=100), db=Depends(get_db_dependency())
):
    host = await get_host_by_id(db, host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    events = await get_host_events_query(db, host_id, limit)
    return events


async def query_hosts(db, status_filter, cloud_provider, limit, offset):
    pass


async def get_host_by_id(db, host_id):
    pass


async def get_host_events_query(db, host_id, limit):
    pass

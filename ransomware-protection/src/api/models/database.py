from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class DetectionType(str, Enum):
    BEHAVIORAL = "behavioral"
    SIGNATURE = "signature"
    ANOMALY = "anomaly"
    HEURISTIC = "heuristic"


class HostStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    QUARANTINED = "quarantined"
    COMPROMISED = "compromised"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    hosts: Mapped[list["Host"]] = relationship("Host", back_populates="organization")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="analyst")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")


class Host(Base):
    __tablename__ = "hosts"
    __table_args__ = (Index("idx_hostname", "hostname"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    os_type: Mapped[str] = mapped_column(String(100), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=HostStatus.ONLINE)
    cloud_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cloud_instance_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"))
    agent_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="hosts")
    events: Mapped[list["SecurityEvent"]] = relationship("SecurityEvent", back_populates="host")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="host")


class SecurityEvent(Base):
    __tablename__ = "security_events"
    __table_args__ = (Index("idx_event_timestamp", "timestamp"), Index("idx_event_host", "host_id"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(Integer, ForeignKey("hosts.id"))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_source: Mapped[str] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), default="info")
    process_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    process_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    user: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    destination_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    ai_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_detection_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    host: Mapped["Host"] = relationship("Host", back_populates="events")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("idx_alert_status", "status"),
        Index("idx_alert_threat_level", "threat_level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"))
    host_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("hosts.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Text] = mapped_column(Text, nullable=True)
    threat_level: Mapped[str] = mapped_column(String(50), default=ThreatLevel.MEDIUM)
    status: Mapped[str] = mapped_column(String(50), default=AlertStatus.NEW)
    detection_type: Mapped[str] = mapped_column(String(50), nullable=True)
    attack_vector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    affected_systems: Mapped[list] = mapped_column(JSON, nullable=True)
    recommended_actions: Mapped[list] = mapped_column(JSON, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    false_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_to: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="alerts")
    host: Mapped[Optional["Host"]] = relationship("Host", back_populates="alerts")
    timeline: Mapped[list["AlertTimeline"]] = relationship("AlertTimeline", back_populates="alert")
    indicators: Mapped[list["IndicatorOfCompromise"]] = relationship(
        "IndicatorOfCompromise", back_populates="alert"
    )


class AlertTimeline(Base):
    __tablename__ = "alert_timeline"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[int] = mapped_column(Integer, ForeignKey("alerts.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    alert: Mapped["Alert"] = relationship("Alert", back_populates="timeline")


class IndicatorOfCompromise(Base):
    __tablename__ = "indicators_of_compromise"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[int] = mapped_column(Integer, ForeignKey("alerts.id"))
    ioc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    false_positive: Mapped[bool] = mapped_column(Boolean, default=False)

    alert: Mapped["Alert"] = relationship("Alert", back_populates="indicators")


class ThreatIntelligence(Base):
    __tablename__ = "threat_intelligence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    threat_type: Mapped[str] = mapped_column(String(100), nullable=False)
    indicator: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(50), default="medium")
    description: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("idx_audit_timestamp", "timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

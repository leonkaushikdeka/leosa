import os
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    name: str = "Ransomware Protection Platform"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 4
    log_level: str = "INFO"


class PostgresConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    username: str = "ransomware_protect"
    password: str = ""
    name: str = "ransomware_protection"
    pool_size: int = 20
    max_overflow: int = 40
    echo: bool = False

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""
    decode_responses: bool = True


class KafkaConfig(BaseModel):
    bootstrap_servers: list[str] = ["localhost:9092"]
    topics: Dict[str, str] = Field(
        default_factory=lambda: {
            "events": "ransomware.events",
            "alerts": "ransomware.alerts",
            "responses": "ransomware.responses",
        }
    )
    consumer_group: str = "ransomware-protection"
    auto_offset_reset: str = "latest"


class ElasticsearchConfig(BaseModel):
    hosts: list[str] = ["http://localhost:9200"]
    index: str = "ransomware-logs"
    session_id: str = "ransomware-protection"
    bulk_size: int = 5000
    flush_interval: int = 5


class MLConfig(BaseModel):
    model_path: str = "models/"
    model_type: str = "ensemble"
    detection_threshold: float = 0.85
    batch_size: int = 256
    inference_timeout: float = 5.0
    gpu_enabled: bool = False


class JWTConfig(BaseModel):
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


class SecurityConfig(BaseModel):
    encryption_algorithm: str = "AES-256-GCM"
    key_rotation_days: int = 90
    jwt: JWTConfig = Field(default_factory=JWTConfig)
    rate_limiting_enabled: bool = True
    requests_per_minute: int = 100
    burst_size: int = 20


class CloudProviderConfig(BaseModel):
    enabled: bool = False
    region: str = ""
    access_key: str = ""
    secret_key: str = ""


class AWSConfig(CloudProviderConfig):
    iam_role: str = ""


class AzureConfig(BaseModel):
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    subscription_id: str = ""


class GCPConfig(BaseModel):
    project_id: str = ""
    credentials_path: str = ""


class CloudProvidersConfig(BaseModel):
    aws: AWSConfig = Field(default_factory=AWSConfig)
    azure: AzureConfig = Field(default_factory=AzureConfig)
    gcp: GCPConfig = Field(default_factory=GCPConfig)


class FileExtensionRisk(BaseModel):
    extension: str
    risk_score: float


class ProcessBehaviorRisk(BaseModel):
    pattern: str
    threshold: int
    time_window_seconds: int
    risk_score: float


class DetectionHeuristicsConfig(BaseModel):
    file_extension_risk: list[FileExtensionRisk] = Field(default_factory=list)
    process_behavior_risk: list[ProcessBehaviorRisk] = Field(default_factory=list)


class DetectionConfig(BaseModel):
    scan_interval_seconds: int = 60
    real_time_enabled: bool = True
    heuristics: DetectionHeuristicsConfig = Field(default_factory=DetectionHeuristicsConfig)


class ResponseActionConfig(BaseModel):
    name: str
    enabled: bool = True
    priority: int = 1
    always_run: bool = False


class ResponseConfig(BaseModel):
    auto_response_enabled: bool = True
    quarantine_enabled: bool = True
    backup_before_action: bool = True
    escalation_timeout_seconds: int = 300
    actions: list[ResponseActionConfig] = Field(default_factory=list)


class BackupConfig(BaseModel):
    provider: str = "s3"
    schedule: str = "0 */4 * * *"
    retention_days: int = 30
    compression: bool = True
    encryption: bool = True


class PrometheusConfig(BaseModel):
    enabled: bool = True
    port: int = 9090


class HealthCheckConfig(BaseModel):
    enabled: bool = True
    interval_seconds: int = 30


class MetricsConfig(BaseModel):
    enabled: bool = True
    export_interval_seconds: int = 15


class MonitoringConfig(BaseModel):
    prometheus: PrometheusConfig = Field(default_factory=PrometheusConfig)
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)


class ComplianceConfig(BaseModel):
    standards: list[str] = Field(default_factory=lambda: ["GDPR", "DPDPA", "ISO27001", "SOC2"])
    audit_log_retention_days: int = 365
    data_retention_days: int = 90


class FrontendConfig(BaseModel):
    api_url: str = "http://localhost:8080"
    refresh_interval: int = 5000
    theme: str = "dark"
    notifications: bool = True


class AgentConfig(BaseModel):
    heartbeat_interval: int = 30
    event_batch_size: int = 100
    max_queue_size: int = 10000
    offline_buffer_size: int = 1000


class Settings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    database: PostgresConfig = Field(default_factory=PostgresConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    kafka: KafkaConfig = Field(default_factory=KafkaConfig)
    elasticsearch: ElasticsearchConfig = Field(default_factory=ElasticsearchConfig)
    ml: MLConfig = Field(default_factory=MLConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    cloud_providers: CloudProvidersConfig = Field(default_factory=CloudProvidersConfig)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    response: ResponseConfig = Field(default_factory=ResponseConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)
    frontend: FrontendConfig = Field(default_factory=FrontendConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)


def load_yaml_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    if config_path is None:
        config_path = os.environ.get(
            "CONFIG_PATH", str(Path(__file__).parent.parent.parent / "config" / "settings.yaml")
        )

    config_file = Path(config_path)
    if not config_file.exists():
        return {}

    with open(config_file, "r") as f:
        return yaml.safe_load(f) or {}


def resolve_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    resolved = {}
    for key, value in config.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_key = value[2:-1]
            resolved[key] = os.environ.get(env_key, "")
        elif isinstance(value, dict):
            resolved[key] = resolve_env_vars(value)
        else:
            resolved[key] = value
    return resolved


@lru_cache()
def get_settings() -> Settings:
    config = load_yaml_config()
    config = resolve_env_vars(config)
    return Settings(**config)

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field

from src.core.config import get_settings
from src.core.kafka import publish_event
from src.core.redis import cache

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class EventContext:
    event_id: str
    host_id: int
    event_type: str
    timestamp: datetime
    raw_data: Dict[str, Any]
    risk_score: float = 0.0
    detection_type: str = "unknown"
    indicators: list = field(default_factory=list)
    processed: bool = False


class EventPipeline:
    def __init__(self):
        self.stages: list[Callable] = []
        self.event_buffer: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self.processing_stats = defaultdict(int)
        self._running = False

    def add_stage(self, stage: Callable):
        self.stages.append(stage)
        return self

    async def start(self):
        self._running = True
        asyncio.create_task(self._process_events())
        logger.info("Event pipeline started")

    async def stop(self):
        self._running = False
        logger.info("Event pipeline stopped")

    async def ingest(self, event_data: Dict[str, Any]):
        context = EventContext(
            event_id=str(event_data.get("id", "")),
            host_id=event_data.get("host_id", 0),
            event_type=event_data.get("event_type", "unknown"),
            timestamp=datetime.utcnow(),
            raw_data=event_data,
        )
        await self.event_buffer.put(context)

    async def _process_events(self):
        while self._running:
            try:
                context = await asyncio.wait_for(self.event_buffer.get(), timeout=1.0)
                await self._run_pipeline(context)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def _run_pipeline(self, context: EventContext):
        for stage in self.stages:
            try:
                await stage(context)
                if context.processed:
                    break
            except Exception as e:
                logger.error(f"Stage {stage.__name__} error: {e}")

        self.processing_stats["total_processed"] += 1
        if context.risk_score >= 0.8:
            self.processing_stats["high_risk_detected"] += 1


class EventNormalizer:
    async def __call__(self, context: EventContext):
        raw = context.raw_data

        normalized = {
            "event_type": raw.get("event_type", "unknown").lower(),
            "process_name": raw.get("process_name", "").lower(),
            "file_path": raw.get("file_path", "").lower(),
            "user": raw.get("user", ""),
            "action": raw.get("action", ""),
            "source_ip": raw.get("source_ip", ""),
            "destination_ip": raw.get("destination_ip", ""),
            "timestamp": context.timestamp.isoformat(),
            "host_id": context.host_id,
        }

        context.raw_data = normalized
        logger.debug(f"Normalized event: {normalized['event_type']}")


class ThreatIntelligenceChecker:
    async def __call__(self, context: EventContext):
        iocs = await self._check_iocs(context.raw_data)
        if iocs:
            context.risk_score = max(context.risk_score, 0.9)
            context.indicators.extend(iocs)
            logger.warning(f"IOC match found: {iocs}")

    async def _check_iocs(self, event_data: Dict[str, Any]) -> list:
        cache_key = f"ioc:{event_data.get('file_hash', '')}"
        cached_ioc = await cache.get(cache_key)
        if cached_ioc:
            return [cached_ioc]

        file_hash = event_data.get("file_hash", "")
        process_name = event_data.get("process_name", "")

        known_iocs = []
        if file_hash:
            pass

        return known_iocs


class BehaviorAnalyzer:
    def __init__(self):
        self.event_counts: Dict[int, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

    async def __call__(self, context: EventContext):
        host_events = self.event_counts[context.host_id]
        current_time = context.timestamp

        time_window = 60
        host_events[context.event_type] = [
            t for t in host_events[context.event_type] if (current_time - t).seconds < time_window
        ]
        host_events[context.event_type].append(current_time)

        count = len(host_events[context.event_type])
        if context.event_type == "file_modification" and count > 100:
            context.risk_score = max(context.risk_score, 0.85)
            context.indicators.append("High rate of file modifications")

        if context.event_type == "process_termination" and count > 50:
            context.risk_score = max(context.risk_score, 0.8)
            context.indicators.append("Mass process termination detected")


class RansomwareDetector:
    def __init__(self):
        self.ml_models = None

    def set_ml_models(self, models):
        self.ml_models = models

    async def __call__(self, context: EventContext):
        if self.ml_models and self.ml_models.is_inference_available():
            result = await self.ml_models.detect(context.raw_data)
            context.risk_score = max(context.risk_score, result["risk_score"])
            context.detection_type = result["detection_type"]
            context.indicators.extend(result.get("indicators", []))
        else:
            await self._heuristic_detection(context)

    async def _heuristic_detection(self, context: EventContext):
        data = context.raw_data
        score = 0.0

        ransomware_extensions = [".encrypted", ".locked", ".ransom", ".crypted"]
        file_path = data.get("file_path", "")
        for ext in ransomware_extensions:
            if ext in file_path:
                score = 0.95
                break

        suspicious_processes = ["vssadmin", "bcdedit", "cipher"]
        process_name = data.get("process_name", "")
        for proc in suspicious_processes:
            if proc in process_name:
                score = max(score, 0.85)
                context.indicators.append(f"Suspicious process: {proc}")

        if score > 0:
            context.risk_score = max(context.risk_score, score)
            context.detection_type = "heuristic"


class AlertGenerator:
    def __init__(self):
        self.threshold = settings.ml.detection_threshold

    async def __call__(self, context: EventContext):
        if context.risk_score >= self.threshold:
            alert_data = {
                "title": f"Ransomware Detected: {context.detection_type.upper()}",
                "description": f"High-risk activity detected with score {context.risk_score:.2f}",
                "threat_level": self._get_threat_level(context.risk_score),
                "host_id": context.host_id,
                "detection_type": context.detection_type,
                "risk_score": context.risk_score,
                "confidence_score": context.risk_score,
                "recommended_actions": self._get_actions(context.risk_score),
                "indicators": context.indicators,
                "timestamp": datetime.utcnow().isoformat(),
            }

            await publish_event(
                settings.kafka.topics["alerts"], key=str(context.event_id), value=alert_data
            )

            context.processed = True
            logger.warning(f"Alert generated for host {context.host_id}")

    def _get_threat_level(self, score: float) -> str:
        if score >= 0.9:
            return "critical"
        elif score >= 0.7:
            return "high"
        elif score >= 0.5:
            return "medium"
        return "low"

    def _get_actions(self, score: float) -> list:
        actions = ["Document the incident"]
        if score >= 0.8:
            actions = [
                "Isolate host from network immediately",
                "Terminate suspicious processes",
                "Preserve forensic evidence",
                "Notify security team",
            ] + actions
        elif score >= 0.6:
            actions = ["Enable enhanced monitoring", "Review recent system changes"] + actions
        return actions


def create_pipeline(ml_models=None) -> EventPipeline:
    pipeline = EventPipeline()

    pipeline.add_stage(EventNormalizer())
    pipeline.add_stage(ThreatIntelligenceChecker())
    pipeline.add_stage(BehaviorAnalyzer())

    detector = RansomwareDetector()
    detector.set_ml_models(ml_models)
    pipeline.add_stage(detector)

    pipeline.add_stage(AlertGenerator())

    return pipeline

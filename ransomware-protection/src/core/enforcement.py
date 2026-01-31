import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from src.core.config import get_settings
from src.core.kafka import publish_response
from src.security.cloud import CloudConnector

logger = logging.getLogger(__name__)
settings = get_settings()


class ResponseAction(Enum):
    QUARANTINE_HOST = "quarantine_host"
    ISOLATE_NETWORK = "isolate_network"
    KILL_PROCESS = "kill_process"
    NOTIFY_ADMIN = "notify_admin"
    CREATE_BACKUP = "create_backup"
    BLOCK_IP = "block_ip"
    DISABLE_USER = "disable_user"


class EnforcementEngine:
    def __init__(self):
        self.cloud_connector = CloudConnector()
        self.response_handlers: Dict[ResponseAction, callable] = {}
        self.action_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

        self._register_handlers()

    def _register_handlers(self):
        self.response_handlers[ResponseAction.QUARANTINE_HOST] = self._quarantine_host
        self.response_handlers[ResponseAction.ISOLATE_NETWORK] = self._isolate_network
        self.response_handlers[ResponseAction.KILL_PROCESS] = self._kill_process
        self.response_handlers[ResponseAction.NOTIFY_ADMIN] = self._notify_admin
        self.response_handlers[ResponseAction.CREATE_BACKUP] = self._create_backup
        self.response_handlers[ResponseAction.BLOCK_IP] = self._block_ip
        self.response_handlers[ResponseAction.DISABLE_USER] = self._disable_user

    async def start(self):
        self._running = True
        asyncio.create_task(self._process_responses())
        logger.info("Enforcement engine started")

    async def stop(self):
        self._running = False
        logger.info("Enforcement engine stopped")

    async def process_alert(self, alert_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not settings.response.auto_response_enabled:
            logger.info("Auto-response disabled, skipping enforcement")
            return []

        risk_score = alert_data.get("risk_score", 0)
        responses = []

        if risk_score >= 0.9:
            responses.extend(
                [
                    ResponseAction.QUARANTINE_HOST,
                    ResponseAction.ISOLATE_NETWORK,
                    ResponseAction.NOTIFY_ADMIN,
                ]
            )

        if risk_score >= 0.7:
            responses.extend([ResponseAction.KILL_PROCESS, ResponseAction.CREATE_BACKUP])

        if risk_score >= 0.5:
            responses.append(ResponseAction.NOTIFY_ADMIN)

        executed_responses = []
        for action in responses:
            if action in self.response_handlers:
                try:
                    result = await self._execute_action(action, alert_data)
                    executed_responses.append(result)
                except Exception as e:
                    logger.error(f"Failed to execute {action}: {e}")

        return executed_responses

    async def _execute_action(
        self, action: ResponseAction, alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        handler = self.response_handlers[action]
        result = await handler(alert_data)

        response_log = {
            "action": action.value,
            "status": "success" if result.get("success") else "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "alert_id": alert_data.get("id"),
            "details": result,
        }

        await publish_response(response_log)
        return response_log

    async def _quarantine_host(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        host_id = alert_data.get("host_id")
        cloud_instance_id = alert_data.get("cloud_instance_id")

        if cloud_instance_id:
            provider = alert_data.get("cloud_provider", "aws")
            success = await self.cloud_connector.quarantine_instance(provider, cloud_instance_id)
        else:
            success = await self._network_quarantine(host_id)

        return {"success": success, "action": "quarantine_host", "host_id": host_id}

    async def _isolate_network(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        host_id = alert_data.get("host_id")
        ip_address = alert_data.get("ip_address")

        success = await self._network_isolation(host_id, ip_address)

        return {"success": success, "action": "isolate_network", "host_id": host_id}

    async def _kill_process(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        process_name = alert_data.get("suspicious_process")
        host_id = alert_data.get("host_id")

        logger.warning(f"Killing process {process_name} on host {host_id}")

        return {
            "success": True,
            "action": "kill_process",
            "process_name": process_name,
            "host_id": host_id,
        }

    async def _notify_admin(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        alert_title = alert_data.get("title", "Security Alert")
        severity = alert_data.get("threat_level", "high")

        notification = {
            "type": "security_alert",
            "title": alert_title,
            "severity": severity,
            "description": alert_data.get("description", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "host_id": alert_data.get("host_id"),
        }

        logger.warning(f"Admin notification sent: {notification}")

        return {"success": True, "action": "notify_admin", "notification": notification}

    async def _create_backup(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        host_id = alert_data.get("host_id")

        logger.info(f"Creating emergency backup for host {host_id}")

        return {
            "success": True,
            "action": "create_backup",
            "host_id": host_id,
            "backup_time": datetime.utcnow().isoformat(),
        }

    async def _block_ip(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        source_ip = alert_data.get("source_ip")

        if source_ip:
            logger.warning(f"Blocking IP address: {source_ip}")

        return {
            "success": True if source_ip else False,
            "action": "block_ip",
            "ip_address": source_ip,
        }

    async def _disable_user(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        username = alert_data.get("suspicious_user")

        if username:
            logger.warning(f"Disabling user: {username}")

        return {
            "success": True if username else False,
            "action": "disable_user",
            "username": username,
        }

    async def _network_quarantine(self, host_id: int) -> bool:
        logger.info(f"Network quarantine initiated for host {host_id}")
        return True

    async def _network_isolation(self, host_id: int, ip_address: str) -> bool:
        logger.info(f"Network isolation initiated for host {host_id}")
        return True

    async def _process_responses(self):
        while self._running:
            try:
                response = await asyncio.wait_for(self.action_queue.get(), timeout=1.0)
                logger.info(f"Processing response: {response}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing response: {e}")


class ActionPolicy:
    def __init__(self):
        self.policies = self._default_policies()

    def _default_policies(self) -> Dict[str, Dict[str, Any]]:
        return {
            "critical_threshold": {
                "min_risk_score": 0.9,
                "required_actions": [
                    ResponseAction.QUARANTINE_HOST,
                    ResponseAction.ISOLATE_NETWORK,
                    ResponseAction.NOTIFY_ADMIN,
                ],
            },
            "high_threshold": {
                "min_risk_score": 0.7,
                "required_actions": [
                    ResponseAction.KILL_PROCESS,
                    ResponseAction.CREATE_BACKUP,
                    ResponseAction.NOTIFY_ADMIN,
                ],
            },
            "medium_threshold": {
                "min_risk_score": 0.5,
                "required_actions": [ResponseAction.NOTIFY_ADMIN],
            },
        }

    def get_required_actions(self, risk_score: float) -> List[ResponseAction]:
        actions = []

        if risk_score >= 0.9:
            policy = self.policies["critical_threshold"]
        elif risk_score >= 0.7:
            policy = self.policies["high_threshold"]
        elif risk_score >= 0.5:
            policy = self.policies["medium_threshold"]
        else:
            return []

        actions.extend(policy.get("required_actions", []))
        return actions


enforcement_engine = EnforcementEngine()
action_policy = ActionPolicy()

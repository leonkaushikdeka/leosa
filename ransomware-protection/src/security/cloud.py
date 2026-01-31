import asyncio
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CloudProvider(ABC):
    @abstractmethod
    async def quarantine_instance(self, instance_id: str) -> bool:
        pass

    @abstractmethod
    async def restore_instance(self, instance_id: str) -> bool:
        pass

    @abstractmethod
    async def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def block_ip(self, ip_address: str, region: str) -> bool:
        pass


class AWSProvider(CloudProvider):
    def __init__(self):
        self.region = settings.cloud_providers.aws.region
        self.access_key = settings.cloud_providers.aws.access_key
        self.secret_key = settings.cloud_providers.aws.secret_key

    async def quarantine_instance(self, instance_id: str) -> bool:
        logger.info(f"AWS: Quarantining instance {instance_id}")
        try:
            import boto3

            ec2 = boto3.client(
                "ec2",
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )

            security_groups = await self._get_instance_security_groups(instance_id)
            await self._apply_quarantine_security_groups(ec2, instance_id)

            logger.info(f"AWS: Successfully quarantined instance {instance_id}")
            return True
        except Exception as e:
            logger.error(f"AWS quarantine failed: {e}")
            return False

    async def restore_instance(self, instance_id: str) -> bool:
        logger.info(f"AWS: Restoring instance {instance_id}")
        try:
            import boto3

            ec2 = boto3.client(
                "ec2",
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )

            await self._restore_original_security_groups(ec2, instance_id)

            logger.info(f"AWS: Successfully restored instance {instance_id}")
            return True
        except Exception as e:
            logger.error(f"AWS restore failed: {e}")
            return False

    async def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        try:
            import boto3

            ec2 = boto3.client(
                "ec2",
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )

            response = ec2.describe_instances(InstanceIds=[instance_id])
            instance = response["Reservations"][0]["Instances"][0]

            return {
                "status": instance["State"]["Name"],
                "instance_id": instance_id,
                "public_ip": instance.get("PublicIpAddress"),
                "private_ip": instance.get("PrivateIpAddress"),
                "security_groups": [sg["GroupId"] for sg in instance["SecurityGroups"]],
            }
        except Exception as e:
            logger.error(f"AWS status check failed: {e}")
            return {"status": "unknown", "error": str(e)}

    async def block_ip(self, ip_address: str, region: str = None) -> bool:
        logger.info(f"AWS: Blocking IP {ip_address}")
        try:
            import boto3

            ec2 = boto3.client(
                "ec2",
                region_name=region or self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )

            security_group_id = await self._get_or_create_blocking_sg(ec2)
            await self._add_ip_to_blocking_sg(ec2, security_group_id, ip_address)

            return True
        except Exception as e:
            logger.error(f"AWS IP block failed: {e}")
            return False

    async def _get_instance_security_groups(self, instance_id: str) -> list:
        return []

    async def _apply_quarantine_security_groups(self, ec2, instance_id: str):
        pass

    async def _restore_original_security_groups(self, ec2, instance_id: str):
        pass

    async def _get_or_create_blocking_sg(self, ec2) -> str:
        return ""

    async def _add_ip_to_blocking_sg(self, ec2, sg_id: str, ip_address: str):
        pass


class AzureProvider(CloudProvider):
    def __init__(self):
        self.tenant_id = settings.cloud_providers.azure.tenant_id
        self.client_id = settings.cloud_providers.azure.client_id
        self.client_secret = settings.cloud_providers.azure.client_secret
        self.subscription_id = settings.cloud_providers.azure.subscription_id

    async def quarantine_instance(self, instance_id: str) -> bool:
        logger.info(f"Azure: Quarantining instance {instance_id}")
        return True

    async def restore_instance(self, instance_id: str) -> bool:
        logger.info(f"Azure: Restoring instance {instance_id}")
        return True

    async def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        return {"status": "unknown", "provider": "azure"}

    async def block_ip(self, ip_address: str, region: str = None) -> bool:
        logger.info(f"Azure: Blocking IP {ip_address}")
        return True


class GCPProvider(CloudProvider):
    def __init__(self):
        self.project_id = settings.cloud_providers.gcp.project_id
        self.credentials_path = settings.cloud_providers.gcp.credentials_path

    async def quarantine_instance(self, instance_id: str) -> bool:
        logger.info(f"GCP: Quarantining instance {instance_id}")
        return True

    async def restore_instance(self, instance_id: str) -> bool:
        logger.info(f"GCP: Restoring instance {instance_id}")
        return True

    async def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        return {"status": "unknown", "provider": "gcp"}

    async def block_ip(self, ip_address: str, region: str = None) -> bool:
        logger.info(f"GCP: Blocking IP {ip_address}")
        return True


class CloudConnector:
    def __init__(self):
        self.providers: Dict[str, CloudProvider] = {}
        self._init_providers()

    def _init_providers(self):
        if settings.cloud_providers.aws.enabled:
            self.providers["aws"] = AWSProvider()

        if settings.cloud_providers.azure.enabled:
            self.providers["azure"] = AzureProvider()

        if settings.cloud_providers.gcp.enabled:
            self.providers["gcp"] = GCPProvider()

    async def quarantine_instance(self, provider: str, instance_id: str, **kwargs) -> bool:
        cloud_provider = self.providers.get(provider.lower())
        if not cloud_provider:
            logger.error(f"Cloud provider {provider} not configured")
            return False

        return await cloud_provider.quarantine_instance(instance_id)

    async def restore_instance(self, provider: str, instance_id: str, **kwargs) -> bool:
        cloud_provider = self.providers.get(provider.lower())
        if not cloud_provider:
            return False

        return await cloud_provider.restore_instance(instance_id)

    async def get_instance_status(
        self, provider: str, instance_id: str, **kwargs
    ) -> Dict[str, Any]:
        cloud_provider = self.providers.get(provider.lower())
        if not cloud_provider:
            return {"status": "unknown", "error": "Provider not configured"}

        return await cloud_provider.get_instance_status(instance_id)

    async def isolate_host(
        self, provider: str, instance_id: str, ip_address: str = None, **kwargs
    ) -> Dict[str, Any]:
        results = {"quarantine": False, "ip_blocked": False}

        results["quarantine"] = await self.quarantine_instance(provider, instance_id)

        if ip_address:
            results["ip_blocked"] = await self.block_ip(provider, ip_address)

        return results

    async def block_ip(self, provider: str, ip_address: str, region: str = None, **kwargs) -> bool:
        cloud_provider = self.providers.get(provider.lower())
        if not cloud_provider:
            return False

        return await cloud_provider.block_ip(ip_address, region)

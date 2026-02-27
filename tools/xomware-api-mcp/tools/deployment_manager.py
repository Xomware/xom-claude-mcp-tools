"""Xomware deployment manager tool."""

import os
from typing import Dict, Any, Optional
import httpx
from loguru import logger


class DeploymentManager:
    """Manages Xomware deployments."""

    def __init__(self, auth_manager):
        """Initialize deployment manager.

        Args:
            auth_manager: Authentication manager instance
        """
        self.auth_manager = auth_manager
        self.base_url = os.getenv("XOMWARE_API_URL", "https://api.xomware.com")
        self.auth_hash = os.getenv("XOMWARE_AUTH_HASH")

    async def deploy(
        self, service: str, version: str, environment: str
    ) -> Dict[str, Any]:
        """Deploy a service to an environment.

        Args:
            service: Service name
            version: Version to deploy
            environment: Target environment (dev, staging, prod)

        Returns:
            Deployment result
        """
        try:
            headers = self._get_headers()
            payload = {
                "service": service,
                "version": version,
                "environment": environment,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/deployments/deploy",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()

                deployment = response.json()

                logger.info(f"Deployed {service}:{version} to {environment}")
                return {
                    "status": "success",
                    "service": service,
                    "version": version,
                    "environment": environment,
                    "deployment_id": deployment.get("id"),
                }

        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Error deploying: {e}")
            return {"error": str(e)}

    async def get_status(self, environment: str) -> Dict[str, Any]:
        """Get deployment status for an environment.

        Args:
            environment: Environment name

        Returns:
            Deployment status
        """
        try:
            headers = self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/deployments/status/{environment}",
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()

                status = response.json()

                logger.info(f"Retrieved deployment status for {environment}")
                return {
                    "status": "success",
                    "environment": environment,
                    "deployments": status,
                }

        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Error getting deployment status: {e}")
            return {"error": str(e)}

    async def rollback(
        self, service: str, environment: str, version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rollback a deployment.

        Args:
            service: Service name
            environment: Environment
            version: Optional specific version to rollback to

        Returns:
            Rollback result
        """
        try:
            headers = self._get_headers()
            payload = {
                "service": service,
                "environment": environment,
                "version": version,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/deployments/rollback",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()

                result = response.json()

                logger.info(f"Rolled back {service} in {environment}")
                return {
                    "status": "success",
                    "service": service,
                    "environment": environment,
                    "previous_version": result.get("previous_version"),
                }

        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Error rolling back: {e}")
            return {"error": str(e)}

    async def get_deployment_history(
        self, service: str, limit: int = 10
    ) -> Dict[str, Any]:
        """Get deployment history for a service.

        Args:
            service: Service name
            limit: Number of deployments to return

        Returns:
            Deployment history
        """
        try:
            headers = self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/deployments/history/{service}",
                    params={"limit": limit},
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()

                history = response.json()

                logger.info(f"Retrieved deployment history for {service}")
                return {
                    "status": "success",
                    "service": service,
                    "history": history,
                }

        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Error getting deployment history: {e}")
            return {"error": str(e)}

    async def monitor_deployment(
        self, service: str, environment: str
    ) -> Dict[str, Any]:
        """Monitor a deployment in progress.

        Args:
            service: Service name
            environment: Environment

        Returns:
            Deployment monitoring data
        """
        try:
            headers = self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/deployments/monitor/{service}/{environment}",
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()

                monitoring = response.json()

                logger.info(f"Monitoring deployment of {service}")
                return {
                    "status": "success",
                    "service": service,
                    "environment": environment,
                    "monitoring": monitoring,
                }

        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Error monitoring deployment: {e}")
            return {"error": str(e)}

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication.

        Returns:
            Headers dictionary
        """
        headers = {
            "Content-Type": "application/json",
        }

        if self.auth_hash:
            headers["X-Auth-Hash"] = self.auth_hash

        return headers

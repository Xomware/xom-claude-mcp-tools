"""Xomware status manager tool."""

import os
from typing import Dict, Any
import httpx
from loguru import logger


class StatusManager:
    """Manages Xomware system status."""

    def __init__(self, auth_manager):
        """Initialize status manager.

        Args:
            auth_manager: Authentication manager instance
        """
        self.auth_manager = auth_manager
        self.base_url = os.getenv("XOMWARE_API_URL", "https://api.xomware.com")
        self.auth_hash = os.getenv("XOMWARE_AUTH_HASH")

    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status.

        Returns:
            System status information
        """
        try:
            headers = self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/status/system",
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()

                status = response.json()

                logger.info("Retrieved system status")
                return {
                    "status": "success",
                    "system_status": status,
                }

        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}

    async def get_service_status(self, service: str) -> Dict[str, Any]:
        """Get status of a specific service.

        Args:
            service: Service name

        Returns:
            Service status
        """
        try:
            headers = self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/status/services/{service}",
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()

                status = response.json()

                logger.info(f"Retrieved status for service: {service}")
                return {
                    "status": "success",
                    "service": service,
                    "service_status": status,
                }

        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {"error": str(e)}

    async def get_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics for all services.

        Returns:
            Health metrics
        """
        try:
            headers = self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/status/health",
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()

                metrics = response.json()

                logger.info("Retrieved health metrics")
                return {
                    "status": "success",
                    "metrics": metrics,
                }

        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Error getting health metrics: {e}")
            return {"error": str(e)}

    async def update_status(
        self, component: str, status: str, message: str = ""
    ) -> Dict[str, Any]:
        """Update component status.

        Args:
            component: Component name
            status: Status (operational, degraded, down)
            message: Optional status message

        Returns:
            Update result
        """
        try:
            headers = self._get_headers()
            payload = {
                "component": component,
                "status": status,
                "message": message,
            }

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/status/update",
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()

                logger.info(f"Updated status for {component}: {status}")
                return {
                    "status": "success",
                    "component": component,
                    "new_status": status,
                }

        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Error updating status: {e}")
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

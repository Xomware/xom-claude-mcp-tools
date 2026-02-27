"""API key authentication manager."""

import hashlib
from typing import Optional, Dict, Set
from loguru import logger
import os


class APIKeyManager:
    """Manages API key validation and access control."""

    def __init__(self):
        """Initialize API key manager."""
        self.valid_keys: Dict[str, Dict[str, any]] = {}
        self.revoked_keys: Set[str] = set()
        self._load_keys_from_env()

    def _load_keys_from_env(self):
        """Load API keys from environment variables."""
        github_token = os.getenv("GITHUB_TOKEN")
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        xomware_key = os.getenv("XOMWARE_API_KEY")

        if github_token:
            self.valid_keys["github"] = {
                "token": github_token,
                "scopes": ["repo", "read:org"],
                "enabled": True,
            }

        if slack_token:
            self.valid_keys["slack"] = {
                "token": slack_token,
                "scopes": ["chat:write", "conversations:read"],
                "enabled": True,
            }

        if xomware_key:
            self.valid_keys["xomware"] = {
                "token": xomware_key,
                "scopes": ["board:read", "board:write", "status:read"],
                "enabled": True,
            }

    def validate_key(self, key: str, service: Optional[str] = None) -> bool:
        """Validate an API key.

        Args:
            key: API key to validate
            service: Optional service name to validate for specific service

        Returns:
            True if key is valid, False otherwise
        """
        if key in self.revoked_keys:
            logger.warning(f"Access attempt with revoked key")
            return False

        if service and service in self.valid_keys:
            return self.valid_keys[service]["token"] == key

        # Check if key matches any service
        for service_key in self.valid_keys.values():
            if service_key["token"] == key and service_key.get("enabled"):
                return True

        logger.warning(f"Invalid API key attempted")
        return False

    def get_token(self, service: str) -> Optional[str]:
        """Get token for a specific service.

        Args:
            service: Service name (github, slack, xomware)

        Returns:
            Token or None if not configured
        """
        if service in self.valid_keys and self.valid_keys[service].get("enabled"):
            return self.valid_keys[service]["token"]
        return None

    def revoke_key(self, key: str):
        """Revoke an API key.

        Args:
            key: API key to revoke
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        self.revoked_keys.add(key_hash)
        logger.info(f"API key revoked: {key_hash[:8]}...")

    def has_scope(self, service: str, required_scope: str) -> bool:
        """Check if service has required scope.

        Args:
            service: Service name
            required_scope: Required scope

        Returns:
            True if service has the scope
        """
        if service not in self.valid_keys:
            return False

        scopes = self.valid_keys[service].get("scopes", [])
        return required_scope in scopes

    def add_key(self, service: str, token: str, scopes: list[str]):
        """Add a new API key.

        Args:
            service: Service name
            token: API token
            scopes: List of authorized scopes
        """
        self.valid_keys[service] = {
            "token": token,
            "scopes": scopes,
            "enabled": True,
        }
        logger.info(f"Added API key for service: {service}")

    def disable_service(self, service: str):
        """Disable a service (revoke all its keys).

        Args:
            service: Service name to disable
        """
        if service in self.valid_keys:
            self.valid_keys[service]["enabled"] = False
            logger.info(f"Disabled service: {service}")

    def enable_service(self, service: str):
        """Enable a previously disabled service.

        Args:
            service: Service name to enable
        """
        if service in self.valid_keys:
            self.valid_keys[service]["enabled"] = True
            logger.info(f"Enabled service: {service}")

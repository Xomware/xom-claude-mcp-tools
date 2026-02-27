"""OAuth2 authentication manager."""

import os
import time
from typing import Optional, Dict, Any
from loguru import logger
import jwt
import httpx


class OAuthManager:
    """Manages OAuth2 token lifecycle and validation."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        jwt_secret: Optional[str] = None,
    ):
        """Initialize OAuth manager.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            token_url: Token endpoint URL
            jwt_secret: Secret for JWT signing
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.jwt_secret = jwt_secret or os.getenv("JWT_SECRET", "secret")
        self.tokens: Dict[str, Any] = {}
        self.expiry: Dict[str, float] = {}

    async def get_token(self, scope: str, user_id: Optional[str] = None) -> str:
        """Get a valid OAuth token, refreshing if needed.

        Args:
            scope: OAuth scope
            user_id: User identifier for scoped tokens

        Returns:
            Valid access token
        """
        cache_key = f"{user_id or 'global'}:{scope}"

        # Check if token exists and is still valid
        if cache_key in self.tokens and cache_key in self.expiry:
            if time.time() < self.expiry[cache_key] - 300:  # 5 min buffer
                logger.debug(f"Using cached token for {cache_key}")
                return self.tokens[cache_key]

        # Request new token
        token = await self._request_token(scope, user_id)
        self.tokens[cache_key] = token["access_token"]
        self.expiry[cache_key] = time.time() + token.get("expires_in", 3600)

        logger.info(f"Obtained new token for {cache_key}")
        return self.tokens[cache_key]

    async def _request_token(self, scope: str, user_id: Optional[str] = None) -> Dict:
        """Request a new token from the OAuth provider.

        Args:
            scope: OAuth scope
            user_id: Optional user identifier

        Returns:
            Token response dictionary
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                    "scope": scope,
                    "user_id": user_id,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    def create_jwt(self, claims: Dict[str, Any]) -> str:
        """Create a signed JWT token.

        Args:
            claims: JWT claims

        Returns:
            Encoded JWT token
        """
        payload = {
            "iat": time.time(),
            "exp": time.time() + 3600,
            **claims,
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded claims or None if invalid
        """
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None

    def revoke_token(self, user_id: Optional[str] = None):
        """Revoke cached tokens.

        Args:
            user_id: User ID to revoke tokens for (None = all)
        """
        if user_id is None:
            self.tokens.clear()
            self.expiry.clear()
            logger.info("Revoked all cached tokens")
        else:
            keys_to_remove = [k for k in self.tokens if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self.tokens[key]
                del self.expiry[key]
            logger.info(f"Revoked tokens for user {user_id}")

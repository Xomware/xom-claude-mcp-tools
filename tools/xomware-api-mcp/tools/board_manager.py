"""Xomware board management tool."""

import os
from typing import Dict, Any, Optional
import httpx
from loguru import logger


class BoardManager:
    """Manages the Xomware command board."""

    def __init__(self, auth_manager):
        """Initialize board manager.

        Args:
            auth_manager: Authentication manager instance
        """
        self.auth_manager = auth_manager
        self.base_url = os.getenv("XOMWARE_API_URL", "https://api.xomware.com")
        self.auth_hash = os.getenv("XOMWARE_AUTH_HASH")
        self.api_key = auth_manager.get_token("xomware")

    async def get_status(self) -> Dict[str, Any]:
        """Get the current board status.

        Returns:
            Board status with all cards and columns
        """
        try:
            headers = self._get_headers()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/status/board",
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()

                board_data = response.json()

                logger.info("Retrieved board status")
                return {
                    "status": "success",
                    "board": board_data,
                }

        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Error getting board status: {e}")
            return {"error": str(e)}

    async def move_card(self, card_id: str, target_column: str) -> Dict[str, Any]:
        """Move a card to a different column.

        Args:
            card_id: Card ID to move
            target_column: Target column name

        Returns:
            Move result
        """
        try:
            headers = self._get_headers()
            payload = {
                "cardId": card_id,
                "targetColumn": target_column,
            }

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/status/board/move",
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()

                result = response.json()

                logger.info(f"Moved card {card_id} to {target_column}")
                return {
                    "status": "success",
                    "card_id": card_id,
                    "target_column": target_column,
                    "result": result,
                }

        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Error moving card: {e}")
            return {"error": str(e)}

    async def add_card(
        self,
        title: str,
        description: str,
        column: str,
        repo_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a new card to the board.

        Args:
            title: Card title
            description: Card description
            column: Column to add to
            repo_hint: Optional repository hint

        Returns:
            Card creation result
        """
        try:
            headers = self._get_headers()
            payload = {
                "title": title,
                "description": description,
                "column": column,
                "repoHint": repo_hint,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/status/board/inbox",
                    json=payload,
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()

                result = response.json()

                logger.info(f"Added card to {column}: {title}")
                return {
                    "status": "success",
                    "card_id": result.get("id"),
                    "title": title,
                }

        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return {"error": f"API error: {e}"}
        except Exception as e:
            logger.error(f"Error adding card: {e}")
            return {"error": str(e)}

    async def get_column(self, column_name: str) -> Dict[str, Any]:
        """Get all cards in a column.

        Args:
            column_name: Column name

        Returns:
            Cards in the column
        """
        try:
            board = await self.get_status()

            if "error" in board:
                return board

            board_data = board.get("board", {})
            columns = board_data.get("columns", {})

            if column_name in columns:
                logger.info(f"Retrieved column: {column_name}")
                return {
                    "status": "success",
                    "column": column_name,
                    "cards": columns[column_name],
                }
            else:
                return {"error": f"Column not found: {column_name}"}

        except Exception as e:
            logger.error(f"Error getting column: {e}")
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
        elif self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

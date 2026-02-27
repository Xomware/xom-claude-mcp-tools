"""Slack message sender tool."""

from typing import Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from loguru import logger


class MessageSender:
    """Sends messages to Slack channels."""

    def __init__(self, auth_manager):
        """Initialize message sender.

        Args:
            auth_manager: Authentication manager instance
        """
        self.auth_manager = auth_manager
        self.token = auth_manager.get_token("slack")
        if self.token:
            self.client = WebClient(token=self.token)
        else:
            self.client = None

    async def send_message(
        self, channel: str, text: str, thread_ts: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message to a Slack channel.

        Args:
            channel: Channel ID or name
            text: Message text
            thread_ts: Optional thread timestamp

        Returns:
            Message send result
        """
        try:
            if not self.client:
                return {"error": "Slack token not configured"}

            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts,
            )

            logger.info(f"Sent message to {channel}")
            return {
                "status": "sent",
                "channel": response["channel"],
                "timestamp": response["ts"],
                "message": text,
            }

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"error": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"error": str(e)}

    async def send_rich_message(
        self,
        channel: str,
        blocks: list,
        thread_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a rich message with blocks to a Slack channel.

        Args:
            channel: Channel ID or name
            blocks: Message blocks (Slack Block Kit format)
            thread_ts: Optional thread timestamp

        Returns:
            Message send result
        """
        try:
            if not self.client:
                return {"error": "Slack token not configured"}

            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                thread_ts=thread_ts,
            )

            logger.info(f"Sent rich message to {channel}")
            return {
                "status": "sent",
                "channel": response["channel"],
                "timestamp": response["ts"],
            }

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"error": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"error": str(e)}

    async def update_message(
        self, channel: str, ts: str, text: str
    ) -> Dict[str, Any]:
        """Update a previously sent message.

        Args:
            channel: Channel ID
            ts: Message timestamp
            text: New message text

        Returns:
            Update result
        """
        try:
            if not self.client:
                return {"error": "Slack token not configured"}

            response = self.client.chat_update(
                channel=channel,
                ts=ts,
                text=text,
            )

            logger.info(f"Updated message in {channel}")
            return {
                "status": "updated",
                "channel": response["channel"],
                "timestamp": response["ts"],
            }

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"error": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            logger.error(f"Error updating message: {e}")
            return {"error": str(e)}

    async def add_reaction(
        self, channel: str, ts: str, emoji: str
    ) -> Dict[str, Any]:
        """Add a reaction to a message.

        Args:
            channel: Channel ID
            ts: Message timestamp
            emoji: Emoji name (without colons)

        Returns:
            Reaction add result
        """
        try:
            if not self.client:
                return {"error": "Slack token not configured"}

            self.client.reactions_add(
                channel=channel,
                timestamp=ts,
                name=emoji,
            )

            logger.info(f"Added reaction to message in {channel}")
            return {
                "status": "reacted",
                "emoji": emoji,
            }

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"error": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            logger.error(f"Error adding reaction: {e}")
            return {"error": str(e)}

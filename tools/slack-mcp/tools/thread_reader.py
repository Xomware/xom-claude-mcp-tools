"""Slack thread reader tool."""

from typing import Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from loguru import logger


class ThreadReader:
    """Reads messages from Slack threads."""

    def __init__(self, auth_manager):
        """Initialize thread reader.

        Args:
            auth_manager: Authentication manager instance
        """
        self.auth_manager = auth_manager
        self.token = auth_manager.get_token("slack")
        if self.token:
            self.client = WebClient(token=self.token)
        else:
            self.client = None

    async def read_thread(self, channel: str, thread_ts: str) -> Dict[str, Any]:
        """Read all messages in a thread.

        Args:
            channel: Channel ID
            thread_ts: Thread timestamp

        Returns:
            Thread messages
        """
        try:
            if not self.client:
                return {"error": "Slack token not configured"}

            response = self.client.conversations_replies(
                channel=channel,
                ts=thread_ts,
                limit=100,
            )

            messages = [
                {
                    "user": msg.get("user", "unknown"),
                    "text": msg.get("text", ""),
                    "timestamp": msg.get("ts", ""),
                    "type": msg.get("type", "message"),
                }
                for msg in response.get("messages", [])
            ]

            logger.info(f"Read thread {thread_ts} in {channel}")
            return {
                "status": "read",
                "channel": channel,
                "thread_ts": thread_ts,
                "message_count": len(messages),
                "messages": messages,
            }

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"error": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            logger.error(f"Error reading thread: {e}")
            return {"error": str(e)}

    async def get_thread_summary(self, channel: str, thread_ts: str) -> Dict[str, Any]:
        """Get a summary of a thread.

        Args:
            channel: Channel ID
            thread_ts: Thread timestamp

        Returns:
            Thread summary
        """
        try:
            if not self.client:
                return {"error": "Slack token not configured"}

            response = self.client.conversations_replies(
                channel=channel,
                ts=thread_ts,
                limit=100,
            )

            messages = response.get("messages", [])
            participants = set()
            text_content = []

            for msg in messages:
                if "user" in msg:
                    participants.add(msg["user"])
                if "text" in msg:
                    text_content.append(msg["text"])

            summary_text = " ".join(text_content[:3])  # First 3 messages

            logger.info(f"Generated summary for thread {thread_ts}")
            return {
                "status": "summarized",
                "thread_ts": thread_ts,
                "message_count": len(messages),
                "participant_count": len(participants),
                "participants": list(participants),
                "summary": summary_text[:500],  # Truncate
            }

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"error": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            logger.error(f"Error summarizing thread: {e}")
            return {"error": str(e)}

    async def search_messages(self, query: str, channel: str = None) -> Dict[str, Any]:
        """Search for messages.

        Args:
            query: Search query
            channel: Optional channel to limit search

        Returns:
            Search results
        """
        try:
            if not self.client:
                return {"error": "Slack token not configured"}

            search_query = query
            if channel:
                search_query += f" in:{channel}"

            response = self.client.search_messages(
                query=search_query,
                count=20,
            )

            matches = [
                {
                    "channel": msg.get("channel", {}),
                    "text": msg.get("text", ""),
                    "timestamp": msg.get("ts", ""),
                    "user": msg.get("user", "unknown"),
                }
                for msg in response.get("messages", [])
            ]

            logger.info(f"Found {len(matches)} messages matching '{query}'")
            return {
                "status": "found",
                "query": query,
                "result_count": len(matches),
                "results": matches,
            }

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"error": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return {"error": str(e)}

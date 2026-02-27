"""Slack notification manager tool."""

from typing import Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from loguru import logger


class NotificationManager:
    """Manages Slack notifications."""

    def __init__(self, auth_manager):
        """Initialize notification manager.

        Args:
            auth_manager: Authentication manager instance
        """
        self.auth_manager = auth_manager
        self.token = auth_manager.get_token("slack")
        if self.token:
            self.client = WebClient(token=self.token)
        else:
            self.client = None

    async def send_notification(
        self,
        channel: str,
        title: str,
        message: str,
        priority: str = "medium",
    ) -> Dict[str, Any]:
        """Send a notification to a Slack channel.

        Args:
            channel: Channel ID or name
            title: Notification title
            message: Notification message
            priority: Priority level (low, medium, high, critical)

        Returns:
            Notification send result
        """
        try:
            if not self.client:
                return {"error": "Slack token not configured"}

            # Color based on priority
            color_map = {
                "low": "#36a64f",
                "medium": "#ffa500",
                "high": "#ff6600",
                "critical": "#ff0000",
            }

            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{title}*\n{message}",
                    },
                },
            ]

            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
            )

            logger.info(f"Sent {priority} notification to {channel}")
            return {
                "status": "sent",
                "channel": response["channel"],
                "timestamp": response["ts"],
                "priority": priority,
            }

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"error": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {"error": str(e)}

    async def send_alert(
        self,
        channel: str,
        alert_title: str,
        alert_message: str,
        details: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send an alert notification.

        Args:
            channel: Channel ID or name
            alert_title: Alert title
            alert_message: Alert message
            details: Optional additional details

        Returns:
            Alert send result
        """
        try:
            if not self.client:
                return {"error": "Slack token not configured"}

            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🚨 *{alert_title}*\n{alert_message}",
                    },
                },
            ]

            # Add details section if provided
            if details:
                details_text = "\n".join(
                    [f"• *{k}*: {v}" for k, v in details.items()]
                )
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": details_text,
                        },
                    }
                )

            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
            )

            logger.info(f"Sent alert to {channel}")
            return {
                "status": "alert_sent",
                "channel": response["channel"],
                "timestamp": response["ts"],
            }

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"error": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return {"error": str(e)}

    async def send_scheduled_notification(
        self,
        channel: str,
        message: str,
        delay_seconds: int,
    ) -> Dict[str, Any]:
        """Schedule a notification to be sent later.

        Args:
            channel: Channel ID
            message: Notification message
            delay_seconds: Delay in seconds

        Returns:
            Scheduling result
        """
        try:
            if not self.client:
                return {"error": "Slack token not configured"}

            import time

            scheduled_time = int(time.time()) + delay_seconds

            response = self.client.chat_scheduleMessage(
                channel=channel,
                text=message,
                post_at=scheduled_time,
            )

            logger.info(f"Scheduled notification for {channel} in {delay_seconds}s")
            return {
                "status": "scheduled",
                "channel": channel,
                "scheduled_time": scheduled_time,
                "message_id": response.get("scheduled_message_id"),
            }

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"error": f"Slack API error: {e.response['error']}"}
        except Exception as e:
            logger.error(f"Error scheduling notification: {e}")
            return {"error": str(e)}

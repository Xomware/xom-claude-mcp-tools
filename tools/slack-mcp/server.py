"""Slack MCP Server - Main entry point."""

import os
import asyncio
from typing import Any
from mcp.server import Server
from mcp.types import Tool
from loguru import logger
from shared.utils import setup_logging, get_logger
from shared.auth import APIKeyManager

# Import Slack tools
from tools.message_sender import MessageSender
from tools.thread_reader import ThreadReader
from tools.notification_manager import NotificationManager

# Setup logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
log = get_logger(__name__)

# Initialize components
auth_manager = APIKeyManager()
message_sender = MessageSender(auth_manager)
thread_reader = ThreadReader(auth_manager)
notification_manager = NotificationManager(auth_manager)

# Create MCP server
server = Server("slack-mcp")


@server.call_tool()
async def handle_tool_call(name: str, arguments: dict) -> Any:
    """Handle tool calls from Claude.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        Tool result
    """
    log.info(f"Tool call: {name} with args: {arguments}")

    try:
        if name == "send_message":
            return await message_sender.send_message(
                arguments.get("channel"),
                arguments.get("text"),
                arguments.get("thread_ts"),
            )
        elif name == "read_thread":
            return await thread_reader.read_thread(
                arguments.get("channel"),
                arguments.get("thread_ts"),
            )
        elif name == "send_notification":
            return await notification_manager.send_notification(
                arguments.get("channel"),
                arguments.get("title"),
                arguments.get("message"),
                arguments.get("priority"),
            )
        else:
            return {"error": f"Unknown tool: {name}"}

    except Exception as e:
        log.error(f"Tool error: {e}")
        return {"error": str(e)}


def define_tools() -> list[Tool]:
    """Define available Slack tools.

    Returns:
        List of tool definitions
    """
    return [
        Tool(
            name="send_message",
            description="Send a message to a Slack channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID or name",
                    },
                    "text": {"type": "string", "description": "Message text"},
                    "thread_ts": {
                        "type": "string",
                        "description": "Optional thread timestamp",
                    },
                },
                "required": ["channel", "text"],
            },
        ),
        Tool(
            name="read_thread",
            description="Read messages from a Slack thread",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID",
                    },
                    "thread_ts": {
                        "type": "string",
                        "description": "Thread timestamp",
                    },
                },
                "required": ["channel", "thread_ts"],
            },
        ),
        Tool(
            name="send_notification",
            description="Send a notification to a Slack channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID or name",
                    },
                    "title": {"type": "string", "description": "Notification title"},
                    "message": {
                        "type": "string",
                        "description": "Notification message",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Notification priority",
                    },
                },
                "required": ["channel", "title", "message"],
            },
        ),
    ]


async def main():
    """Start the Slack MCP server."""
    log.info("Starting Slack MCP server...")

    # Register tools
    for tool in define_tools():
        await server.register_tool(tool)

    # Start server
    async with server:
        log.info(f"Slack MCP server running on port {os.getenv('SERVER_PORT', 8000)}")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())

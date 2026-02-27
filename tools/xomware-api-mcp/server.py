"""Xomware API MCP Server - Main entry point."""

import os
import asyncio
from typing import Any
from mcp.server import Server
from mcp.types import Tool
from loguru import logger
from shared.utils import setup_logging, get_logger
from shared.auth import APIKeyManager

# Import Xomware tools
from tools.board_manager import BoardManager
from tools.status_manager import StatusManager
from tools.deployment_manager import DeploymentManager

# Setup logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
log = get_logger(__name__)

# Initialize components
auth_manager = APIKeyManager()
board_manager = BoardManager(auth_manager)
status_manager = StatusManager(auth_manager)
deployment_manager = DeploymentManager(auth_manager)

# Create MCP server
server = Server("xomware-api-mcp")


@server.call_tool()
async def handle_tool_call(name: str, arguments: dict) -> Any:
    """Handle tool calls from Claude.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        Tool result
    """
    log.info(f"Tool call: {name}")

    try:
        if name == "get_board_status":
            return await board_manager.get_status()
        elif name == "move_card":
            return await board_manager.move_card(
                arguments.get("card_id"),
                arguments.get("column"),
            )
        elif name == "get_deployment_status":
            return await deployment_manager.get_status(
                arguments.get("environment"),
            )
        elif name == "deploy":
            return await deployment_manager.deploy(
                arguments.get("service"),
                arguments.get("version"),
                arguments.get("environment"),
            )
        else:
            return {"error": f"Unknown tool: {name}"}

    except Exception as e:
        log.error(f"Tool error: {e}")
        return {"error": str(e)}


def define_tools() -> list[Tool]:
    """Define available Xomware API tools.

    Returns:
        List of tool definitions
    """
    return [
        Tool(
            name="get_board_status",
            description="Get the current status of the Xomware command board",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="move_card",
            description="Move a card on the board to a different column",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {
                        "type": "string",
                        "description": "Card ID to move",
                    },
                    "column": {
                        "type": "string",
                        "description": "Target column name",
                    },
                },
                "required": ["card_id", "column"],
            },
        ),
        Tool(
            name="get_deployment_status",
            description="Get deployment status for an environment",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "description": "Environment name (dev, staging, prod)",
                    },
                },
                "required": ["environment"],
            },
        ),
        Tool(
            name="deploy",
            description="Deploy a service to an environment",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {"type": "string", "description": "Service name"},
                    "version": {"type": "string", "description": "Version to deploy"},
                    "environment": {
                        "type": "string",
                        "description": "Target environment",
                    },
                },
                "required": ["service", "version", "environment"],
            },
        ),
    ]


async def main():
    """Start the Xomware API MCP server."""
    log.info("Starting Xomware API MCP server...")

    # Register tools
    for tool in define_tools():
        await server.register_tool(tool)

    # Start server
    async with server:
        log.info(f"Xomware API MCP server running on port {os.getenv('SERVER_PORT', 8000)}")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())

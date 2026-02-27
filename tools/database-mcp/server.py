"""Database MCP Server - Main entry point."""

import os
import asyncio
from typing import Any
from mcp.server import Server
from mcp.types import Tool
from loguru import logger
from shared.utils import setup_logging, get_logger
from shared.auth import APIKeyManager

# Import Database tools
from tools.query_executor import QueryExecutor
from tools.update_manager import UpdateManager
from tools.analytics import Analytics

# Setup logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
log = get_logger(__name__)

# Initialize components
auth_manager = APIKeyManager()
query_executor = QueryExecutor()
update_manager = UpdateManager()
analytics = Analytics()

# Create MCP server
server = Server("database-mcp")


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
        if name == "execute_query":
            return await query_executor.execute(
                arguments.get("query"),
                arguments.get("params"),
            )
        elif name == "update_data":
            return await update_manager.update(
                arguments.get("table"),
                arguments.get("data"),
                arguments.get("conditions"),
            )
        elif name == "run_analytics":
            return await analytics.analyze(
                arguments.get("metric"),
                arguments.get("filters"),
                arguments.get("period"),
            )
        else:
            return {"error": f"Unknown tool: {name}"}

    except Exception as e:
        log.error(f"Tool error: {e}")
        return {"error": str(e)}


def define_tools() -> list[Tool]:
    """Define available database tools.

    Returns:
        List of tool definitions
    """
    return [
        Tool(
            name="execute_query",
            description="Execute a database query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query"},
                    "params": {
                        "type": "array",
                        "description": "Query parameters",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="update_data",
            description="Update data in the database",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Table name"},
                    "data": {
                        "type": "object",
                        "description": "Data to update",
                    },
                    "conditions": {
                        "type": "object",
                        "description": "WHERE conditions",
                    },
                },
                "required": ["table", "data", "conditions"],
            },
        ),
        Tool(
            name="run_analytics",
            description="Run analytics and get insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "description": "Metric to analyze"},
                    "filters": {
                        "type": "object",
                        "description": "Filter criteria",
                    },
                    "period": {"type": "string", "description": "Time period"},
                },
                "required": ["metric"],
            },
        ),
    ]


async def main():
    """Start the Database MCP server."""
    log.info("Starting Database MCP server...")

    # Register tools
    for tool in define_tools():
        await server.register_tool(tool)

    # Start server
    async with server:
        log.info(f"Database MCP server running on port {os.getenv('SERVER_PORT', 8000)}")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())

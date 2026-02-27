"""GitHub MCP Server - Main entry point."""

import os
import asyncio
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from loguru import logger
from shared.utils import setup_logging, get_logger
from shared.auth import APIKeyManager

# Import GitHub tools
from tools.pr_reviewer import PRReviewer
from tools.issue_manager import IssueManager
from tools.code_analyzer import CodeAnalyzer

# Setup logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
log = get_logger(__name__)

# Initialize components
auth_manager = APIKeyManager()
pr_reviewer = PRReviewer(auth_manager)
issue_manager = IssueManager(auth_manager)
code_analyzer = CodeAnalyzer(auth_manager)

# Create MCP server
server = Server("github-mcp")


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
        if name == "review_pr":
            return await pr_reviewer.review_pr(
                arguments.get("repo"),
                arguments.get("pr_number"),
            )
        elif name == "create_issue":
            return await issue_manager.create_issue(
                arguments.get("repo"),
                arguments.get("title"),
                arguments.get("body"),
                arguments.get("labels"),
            )
        elif name == "analyze_code":
            return await code_analyzer.analyze(
                arguments.get("repo"),
                arguments.get("path"),
                arguments.get("ref"),
            )
        else:
            return {"error": f"Unknown tool: {name}"}

    except Exception as e:
        log.error(f"Tool error: {e}")
        return {"error": str(e)}


def define_tools() -> list[Tool]:
    """Define available GitHub tools.

    Returns:
        List of tool definitions
    """
    return [
        Tool(
            name="review_pr",
            description="Review a GitHub pull request",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "Repository (owner/name)",
                    },
                    "pr_number": {"type": "integer", "description": "PR number"},
                },
                "required": ["repo", "pr_number"],
            },
        ),
        Tool(
            name="create_issue",
            description="Create a new GitHub issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "Repository (owner/name)",
                    },
                    "title": {"type": "string", "description": "Issue title"},
                    "body": {"type": "string", "description": "Issue body"},
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Issue labels",
                    },
                },
                "required": ["repo", "title"],
            },
        ),
        Tool(
            name="analyze_code",
            description="Analyze code in a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "Repository (owner/name)",
                    },
                    "path": {"type": "string", "description": "File path to analyze"},
                    "ref": {
                        "type": "string",
                        "description": "Git ref (branch/tag/commit)",
                    },
                },
                "required": ["repo", "path"],
            },
        ),
    ]


async def main():
    """Start the GitHub MCP server."""
    log.info("Starting GitHub MCP server...")

    # Register tools
    for tool in define_tools():
        await server.register_tool(tool)

    # Start server
    async with server:
        log.info(f"GitHub MCP server running on port {os.getenv('SERVER_PORT', 8000)}")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())

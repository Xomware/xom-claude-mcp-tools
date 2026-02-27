"""Template for creating custom MCP tools."""

from typing import Dict, Any, Optional
from loguru import logger


class CustomTool:
    """Base template for custom MCP tools.

    Usage:
        1. Copy this file and rename to your_tool.py
        2. Implement the required methods
        3. Update the tool name and description
        4. Register in your MCP server
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize custom tool.

        Args:
            config: Tool configuration dictionary
        """
        self.config = config or {}
        self.name = "custom_tool"
        self.description = "A custom MCP tool"

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            Tool execution result
        """
        try:
            logger.info(f"Executing {self.name} with args: {kwargs}")

            # Implement your tool logic here
            result = {
                "status": "success",
                "message": f"{self.name} executed successfully",
                "data": {},
            }

            return result

        except Exception as e:
            logger.error(f"Error executing {self.name}: {e}")
            return {"error": str(e)}

    async def validate_input(self, **kwargs) -> bool:
        """Validate input arguments.

        Args:
            **kwargs: Arguments to validate

        Returns:
            True if valid, False otherwise
        """
        # Implement validation logic
        return True

    async def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle errors gracefully.

        Args:
            error: Exception that occurred

        Returns:
            Error response
        """
        logger.error(f"Tool error: {error}")
        return {
            "error": str(error),
            "tool": self.name,
            "status": "failed",
        }

    async def get_metadata(self) -> Dict[str, Any]:
        """Get tool metadata.

        Returns:
            Tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": "1.0.0",
            "author": "Xomware",
            "capabilities": [],
        }


# Example: Simple calculator tool
class CalculatorTool(CustomTool):
    """Example custom tool that performs calculations."""

    def __init__(self):
        """Initialize calculator tool."""
        super().__init__()
        self.name = "calculator"
        self.description = "Performs mathematical calculations"

    async def execute(self, operation: str, operands: list[float]) -> Dict[str, Any]:
        """Execute calculation.

        Args:
            operation: Operation to perform (add, subtract, multiply, divide)
            operands: List of operands

        Returns:
            Calculation result
        """
        try:
            if not await self.validate_input(
                operation=operation, operands=operands
            ):
                return {"error": "Invalid input"}

            if operation == "add":
                result = sum(operands)
            elif operation == "subtract":
                result = operands[0] - sum(operands[1:])
            elif operation == "multiply":
                result = 1
                for operand in operands:
                    result *= operand
            elif operation == "divide":
                result = operands[0]
                for operand in operands[1:]:
                    if operand == 0:
                        return {"error": "Division by zero"}
                    result /= operand
            else:
                return {"error": f"Unknown operation: {operation}"}

            logger.info(f"Calculated {operation} of {operands} = {result}")
            return {
                "status": "success",
                "operation": operation,
                "operands": operands,
                "result": result,
            }

        except Exception as e:
            return await self.handle_error(e)

    async def validate_input(self, **kwargs) -> bool:
        """Validate calculator input."""
        operation = kwargs.get("operation")
        operands = kwargs.get("operands", [])

        if operation not in ["add", "subtract", "multiply", "divide"]:
            return False

        if not isinstance(operands, list) or len(operands) < 2:
            return False

        return all(isinstance(op, (int, float)) for op in operands)


# Example: Data formatter tool
class DataFormatterTool(CustomTool):
    """Example tool for formatting data."""

    def __init__(self):
        """Initialize data formatter tool."""
        super().__init__()
        self.name = "data_formatter"
        self.description = "Formats data in various output formats"

    async def execute(self, data: Dict, format: str = "json") -> Dict[str, Any]:
        """Format data.

        Args:
            data: Data to format
            format: Output format (json, csv, yaml, xml)

        Returns:
            Formatted data
        """
        try:
            if format == "json":
                import json

                formatted = json.dumps(data, indent=2)
            elif format == "csv":
                formatted = self._to_csv(data)
            elif format == "yaml":
                import yaml

                formatted = yaml.dump(data)
            else:
                return {"error": f"Unknown format: {format}"}

            logger.info(f"Formatted data as {format}")
            return {
                "status": "success",
                "format": format,
                "data": formatted,
            }

        except Exception as e:
            return await self.handle_error(e)

    def _to_csv(self, data: Dict) -> str:
        """Convert dict to CSV format."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data.keys())
        writer.writeheader()
        writer.writerow(data)
        return output.getvalue()

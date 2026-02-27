# Tool Development Guide

## Creating Custom MCP Tools

This guide covers how to develop new custom tools for the xom-claude-mcp-tools repository.

## Structure

Every tool should follow this structure:

```python
from typing import Dict, Any
from loguru import logger

class MyCustomTool:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.name = "my_custom_tool"
        self.description = "What this tool does"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Main tool execution method."""
        try:
            # Implement tool logic
            result = {}
            logger.info(f"Tool executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool error: {e}")
            return {"error": str(e)}
```

## Step-by-Step Tutorial

### 1. Create Tool File

```bash
cp tools/custom-tools/template.py tools/my-mcp/tools/my_tool.py
```

### 2. Implement Tool Logic

```python
from typing import Dict, Any, Optional
from loguru import logger

class MyTool:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.name = "my_tool"
        self.description = "Performs my custom operation"
    
    async def execute(self, param1: str, param2: int = 10) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Args:
            param1: Required parameter
            param2: Optional parameter with default
            
        Returns:
            Result dictionary
        """
        try:
            # Validate inputs
            if not self.validate_inputs(param1, param2):
                return {"error": "Invalid input"}
            
            # Perform operation
            result = self._process(param1, param2)
            
            logger.info(f"Tool executed: {result}")
            return {
                "status": "success",
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {"error": str(e)}
    
    def validate_inputs(self, param1: str, param2: int) -> bool:
        """Validate tool inputs."""
        if not isinstance(param1, str) or not param1:
            return False
        if not isinstance(param2, int) or param2 < 0:
            return False
        return True
    
    def _process(self, param1: str, param2: int):
        """Internal processing logic."""
        return {
            "param1_processed": param1.upper(),
            "param2_doubled": param2 * 2
        }
```

### 3. Register Tool in Server

Update the MCP server to include your tool:

```python
# In server.py
from tools.my_tool import MyTool

my_tool = MyTool(auth_manager)

@server.call_tool()
async def handle_tool_call(name: str, arguments: dict):
    if name == "my_tool":
        return await my_tool.execute(**arguments)

def define_tools():
    return [
        # ... existing tools ...
        Tool(
            name="my_tool",
            description="Performs my custom operation",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Required parameter",
                    },
                    "param2": {
                        "type": "integer",
                        "description": "Optional parameter",
                        "default": 10,
                    },
                },
                "required": ["param1"],
            },
        ),
    ]
```

## Best Practices

### 1. Error Handling

```python
async def execute(self, **kwargs):
    try:
        # Validate inputs first
        if not self.validate_inputs(kwargs):
            return {
                "error": "Invalid input",
                "error_code": "INVALID_INPUT"
            }
        
        # Execute main logic
        result = await self._process(kwargs)
        
        return {"status": "success", "data": result}
        
    except AuthenticationError as e:
        logger.warning(f"Auth failed: {e}")
        return {"error": str(e), "error_code": "AUTH_FAILED"}
        
    except RateLimitError as e:
        logger.warning(f"Rate limited: {e}")
        return {"error": str(e), "error_code": "RATE_LIMIT"}
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "error_code": "INTERNAL_ERROR"}
```

### 2. Logging

```python
from loguru import logger

# Log important operations
logger.info(f"Starting operation with params: {params}")

# Log warnings for non-critical issues
logger.warning(f"Retry attempt {attempt}")

# Log errors with full context
logger.error(f"Failed to process: {error}", extra={"params": params})

# Don't log sensitive data
logger.info(f"Token: {auth_manager.mask_sensitive(token)}")
```

### 3. Input Validation

```python
def validate_inputs(self, **kwargs) -> bool:
    """Validate all required inputs."""
    required = ["repo", "pr_number"]
    
    # Check required fields
    for field in required:
        if field not in kwargs or not kwargs[field]:
            logger.warning(f"Missing required field: {field}")
            return False
    
    # Type validation
    if not isinstance(kwargs.get("pr_number"), int):
        logger.warning("pr_number must be integer")
        return False
    
    # Range validation
    if kwargs.get("pr_number") < 0:
        logger.warning("pr_number must be positive")
        return False
    
    return True
```

### 4. Async/Await Pattern

```python
# Use async for I/O operations
async def fetch_data(self, url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        return response.json()

# Use async context managers for cleanup
async def database_operation(self):
    session = self.SessionLocal()
    try:
        result = await self._query(session)
        return result
    finally:
        session.close()
```

### 5. Caching

```python
from functools import lru_cache
import time

class MyTool:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def execute(self, key: str):
        # Check cache
        if key in self.cache:
            cached_time, cached_result = self.cache[key]
            if time.time() - cached_time < self.cache_ttl:
                logger.debug(f"Returning cached result for {key}")
                return cached_result
        
        # Execute and cache
        result = await self._fetch(key)
        self.cache[key] = (time.time(), result)
        return result
```

## Testing

### Unit Tests

```python
import pytest
from tools.my_tool import MyTool

@pytest.fixture
def tool():
    return MyTool(auth_manager=None)

@pytest.mark.asyncio
async def test_execute_success(tool):
    result = await tool.execute(param1="test", param2=5)
    assert result["status"] == "success"
    assert result["data"]["param1_processed"] == "TEST"

@pytest.mark.asyncio
async def test_invalid_input(tool):
    result = await tool.execute(param1="", param2=-1)
    assert "error" in result
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_workflow():
    # Test complete workflow with real dependencies
    auth_manager = APIKeyManager()
    tool = MyTool(auth_manager)
    
    result = await tool.execute(param1="test", param2=10)
    assert result["status"] == "success"
```

## Advanced Patterns

### Rate Limiting

```python
import asyncio
from datetime import datetime, timedelta

class RateLimitedTool:
    def __init__(self, requests_per_minute=60):
        self.requests = []
        self.requests_per_minute = requests_per_minute
    
    async def execute(self, **kwargs):
        # Check rate limit
        now = datetime.now()
        self.requests = [
            req_time for req_time in self.requests
            if req_time > now - timedelta(minutes=1)
        ]
        
        if len(self.requests) >= self.requests_per_minute:
            wait_time = 60 - (now - self.requests[0]).seconds
            raise RateLimitError(f"Rate limit exceeded. Retry in {wait_time}s")
        
        self.requests.append(now)
        return await self._process(**kwargs)
```

### Retry Logic

```python
import asyncio

async def execute_with_retry(
    self,
    operation,
    max_attempts=3,
    backoff_factor=2
):
    """Execute operation with exponential backoff retry."""
    for attempt in range(max_attempts):
        try:
            return await operation()
        except TemporaryError as e:
            if attempt == max_attempts - 1:
                raise
            
            wait_time = backoff_factor ** attempt
            logger.warning(
                f"Attempt {attempt + 1} failed, retrying in {wait_time}s"
            )
            await asyncio.sleep(wait_time)
```

### Streaming Results

```python
async def execute_streaming(self, query: str):
    """Stream results instead of loading all in memory."""
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", f"{self.url}/query", params={"q": query}) as response:
            async for chunk in response.aiter_lines():
                yield json.loads(chunk)
```

## Documentation

Always document your tools:

```python
class MyTool:
    """
    Performs custom operations.
    
    This tool integrates with the external API to process data
    and return results in a standardized format.
    
    Attributes:
        auth_manager: Authentication manager instance
        name: Tool identifier
        description: Tool description
    
    Example:
        >>> tool = MyTool(auth_manager)
        >>> result = await tool.execute(param1="value")
        >>> print(result["data"])
    """
    
    async def execute(self, param1: str) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Args:
            param1: Required parameter description
            
        Returns:
            Dictionary with:
                - status: "success" or error details
                - data: Result data (if successful)
                - error: Error message (if failed)
                
        Raises:
            ValidationError: If inputs are invalid
            AuthenticationError: If authentication fails
            
        Example:
            >>> result = await tool.execute(param1="test")
            >>> if result["status"] == "success":
            ...     print(result["data"])
        """
```

## References

- [MCP Protocol Guide](./mcp-protocol.md)
- [Security Guide](./security-guide.md)
- [Custom Tools Template](../tools/custom-tools/template.py)

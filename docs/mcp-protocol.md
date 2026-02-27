# MCP Protocol Guide

## Overview

Model Context Protocol (MCP) is a protocol for Claude to interact with external tools and services. This guide covers how the xom-claude-mcp-tools implements and uses MCP.

## Architecture

```
Claude AI
    ↓
    └─→ MCP Server (xom-mcp-tools)
            ├─→ GitHub Tools
            ├─→ Slack Tools
            ├─→ Database Tools
            └─→ Xomware API Tools
```

## MCP Server Components

### Server Definition

Each MCP server is defined with:
- **Name**: Unique identifier (e.g., `github-mcp`)
- **Version**: Semantic versioning (e.g., `1.0.0`)
- **Tools**: Array of available tools
- **Authentication**: Security configuration

### Tool Schema

Each tool must define:
```json
{
  "name": "tool_name",
  "description": "What this tool does",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "Parameter description"
      }
    },
    "required": ["param1"]
  }
}
```

## Request/Response Flow

### Tool Call Request

```python
{
    "type": "tool_call",
    "tool_name": "review_pr",
    "arguments": {
        "repo": "Xomware/xom-project",
        "pr_number": 42
    }
}
```

### Tool Response

```python
{
    "status": "success",
    "data": {
        "pr_number": 42,
        "title": "Add new feature",
        "author": "john_doe",
        # ... additional data
    }
}
```

## Error Handling

### Standard Error Response

```python
{
    "error": "Description of error",
    "error_code": "INVALID_INPUT",
    "details": {
        # Additional error details
    }
}
```

### Error Codes

- `INVALID_INPUT`: Input validation failed
- `AUTHENTICATION_FAILED`: Auth credentials missing or invalid
- `RATE_LIMIT`: Rate limit exceeded
- `SERVICE_UNAVAILABLE`: External service is down
- `INTERNAL_ERROR`: Unexpected server error

## Authentication

### API Key Authentication

```python
headers = {
    "Authorization": "Bearer {token}",
    "X-API-Key": "{api_key}"
}
```

### OAuth2 Authentication

```python
# Token is obtained and refreshed automatically
token = await oauth_manager.get_token(scope="repo")
headers = {
    "Authorization": f"Bearer {token}"
}
```

## Tool Examples

### GitHub MCP

#### Review PR

```python
await mcp.call_tool("review_pr", {
    "repo": "Xomware/xom-project",
    "pr_number": 42
})
```

Response includes:
- PR metadata (title, author, state)
- Files changed
- Commits
- Existing reviews

#### Create Issue

```python
await mcp.call_tool("create_issue", {
    "repo": "Xomware/xom-project",
    "title": "Bug: Login fails",
    "body": "Detailed bug description...",
    "labels": ["bug", "high-priority"]
})
```

### Slack MCP

#### Send Message

```python
await mcp.call_tool("send_message", {
    "channel": "C1234567",
    "text": "Hello team!"
})
```

#### Read Thread

```python
await mcp.call_tool("read_thread", {
    "channel": "C1234567",
    "thread_ts": "1234567890.123456"
})
```

### Database MCP

#### Execute Query

```python
await mcp.call_tool("execute_query", {
    "query": "SELECT * FROM users WHERE status = :status",
    "params": {"status": "active"}
})
```

### Xomware API MCP

#### Get Board Status

```python
await mcp.call_tool("get_board_status")
```

#### Move Card

```python
await mcp.call_tool("move_card", {
    "card_id": "CARD-123",
    "column": "In Progress"
})
```

## Rate Limiting

### Rate Limits

- **Default**: 60 requests per minute per tool
- **Burst**: 10 requests per second

### Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1672531200
```

### Backoff Strategy

```python
# Exponential backoff when rate limited
for attempt in range(max_attempts):
    try:
        result = await tool.execute()
        return result
    except RateLimitError:
        wait_time = 2 ** attempt  # 1, 2, 4, 8...
        await asyncio.sleep(wait_time)
```

## Monitoring

### Health Checks

```
GET /health
```

Response:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "services": {
        "github": "healthy",
        "slack": "healthy",
        "database": "healthy"
    }
}
```

### Metrics

Prometheus metrics available at `/metrics`:
- `mcp_tool_calls_total`: Total tool calls
- `mcp_tool_errors_total`: Total tool errors
- `mcp_tool_duration_seconds`: Tool execution time
- `mcp_authentication_failures`: Auth failures

## Best Practices

1. **Always validate input** before executing tools
2. **Log sensitive operations** (without logging secrets)
3. **Implement proper error handling** with descriptive messages
4. **Use connection pooling** for database operations
5. **Cache responses** where appropriate (respecting TTLs)
6. **Monitor rate limits** and implement backoff
7. **Test thoroughly** before deploying to production

## Advanced Features

### Streaming Responses

For long-running operations:

```python
async def execute_with_streaming(self, query):
    async for chunk in self.stream_results(query):
        yield chunk
```

### Webhooks

Register webhooks for event notifications:

```python
POST /webhooks/register
{
    "event": "pr_opened",
    "url": "https://example.com/webhook"
}
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check token validity
   - Verify token has required scopes
   - Check token expiration

2. **Rate Limiting**
   - Implement exponential backoff
   - Batch requests where possible
   - Use caching

3. **Service Unavailable**
   - Check service status
   - Verify network connectivity
   - Check firewall rules

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Tool Development Guide](./tool-development.md)
- [Security Guide](./security-guide.md)

# xom-claude-mcp-tools

Production-ready Claude MCP (Model Context Protocol) tools for GitHub, Slack, Database, and Xomware API integration.

## Overview

This repository provides a comprehensive suite of MCP servers and tools that extend Claude's capabilities across multiple platforms and services:

- **GitHub MCP**: PR reviews, issue management, and code analysis
- **Slack MCP**: Message sending, thread management, and notifications
- **Database MCP**: Query execution, updates, and analytics
- **Xomware API MCP**: Board management, status updates, and deployment tracking

## Features

- 🔐 **Secure Authentication**: OAuth2, API keys, and encryption
- 🚀 **Production-Ready**: Error handling, monitoring, and testing
- 🐳 **Docker Support**: Containerized deployment for each tool
- 📚 **Complete Documentation**: Development guides, security protocols, and deployment strategies
- 🧪 **Comprehensive Testing**: Unit tests and integration tests included
- ⚙️ **Infrastructure as Code**: Kubernetes and Terraform configurations

## Quick Start

### Installation

```bash
git clone https://github.com/Xomware/xom-claude-mcp-tools.git
cd xom-claude-mcp-tools
pip install -r requirements.txt
```

### Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Configure your credentials:
```bash
# GitHub
GITHUB_TOKEN=your_token_here

# Slack
SLACK_BOT_TOKEN=your_token_here
SLACK_SIGNING_SECRET=your_secret_here

# Database
DB_HOST=localhost
DB_USER=user
DB_PASSWORD=password
```

### Running Servers

#### Docker Compose (All Services)
```bash
cd deployment
docker-compose up -d
```

#### Individual Servers

```bash
# GitHub MCP
python tools/github-mcp/server.py

# Slack MCP
python tools/slack-mcp/server.py

# Database MCP
python tools/database-mcp/server.py

# Xomware API MCP
python tools/xomware-api-mcp/server.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude AI                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                    MCP Protocol
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼──┐         ┌───▼──┐         ┌──▼───┐
    │GitHub│         │Slack │         │  DB  │
    │ MCP  │         │ MCP  │         │ MCP  │
    └──────┘         └──────┘         └──────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼──────┐   ┌────▼────┐    ┌──────▼──┐
    │GitHub    │   │Slack    │    │Database │
    │Services  │   │Services │    │Services │
    └──────────┘   └─────────┘    └─────────┘
```

## MCP Servers

### GitHub MCP
- **PR review automation**: Automated code review suggestions using Claude
- **Issue management**: Create, update, and close issues programmatically
- **Code analysis**: Analyze code quality, suggest improvements
- **Commit analysis**: Parse commits and generate summaries

**Example**:
```python
# Review a pull request
github_tool.review_pr(owner="xomware", repo="project", pr_number=123)
```

### Slack MCP
- **Send messages**: Post to channels with formatting
- **Thread management**: Read and write in conversation threads
- **User management**: Lookup users and check presence
- **Notification management**: Schedule and manage notifications

**Example**:
```python
# Send a message
slack_tool.send_message(channel="#general", text="Hello Xomware!")

# Thread reply
slack_tool.reply_in_thread(channel="#general", timestamp="123.456", text="Reply text")
```

### Database MCP
- **Query execution**: Run SELECT queries with connection pooling
- **Data updates**: INSERT, UPDATE, DELETE operations
- **Analytics**: Aggregate and summarize data
- **Connection management**: Handle multiple database connections

**Example**:
```python
# Execute a query
db_tool.execute_query(sql="SELECT * FROM users WHERE active=true")

# Update records
db_tool.update_records(table="users", where={"id": 1}, data={"status": "active"})
```

### Xomware API MCP
- **Board management**: Create, update, and move board items
- **Status updates**: Update deployment and project status
- **Deployment tracking**: Monitor deployments and releases
- **Analytics and reporting**: Generate reports and metrics

**Example**:
```python
# Move board item
xomware_tool.move_board_item(board_id=2, card_id=123, target_column="In Progress")

# Update status
xomware_tool.update_status(resource_id="pr-456", status="merged")
```

## Project Structure

```
xom-claude-mcp-tools/
├── tools/
│   ├── github-mcp/
│   ├── slack-mcp/
│   ├── database-mcp/
│   ├── xomware-api-mcp/
│   └── custom-tools/
├── shared/
│   ├── auth/
│   ├── security/
│   └── utils/
├── deployment/
│   ├── docker-compose.yml
│   ├── kubernetes/
│   └── terraform/
├── docs/
├── tests/
├── requirements.txt
├── .env.example
└── LICENSE
```

## Documentation

- [MCP Protocol Guide](./docs/mcp-protocol.md) - Protocol specifications and examples
- [Tool Development](./docs/tool-development.md) - Creating custom tools
- [Security Guide](./docs/security-guide.md) - Authentication and encryption
- [Deployment Guide](./docs/deployment.md) - Production deployment strategies

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for:

- Development setup instructions
- How to add new MCP tools
- Code style and testing requirements
- Pull request process

**Quick start**:
```bash
# Fork the repo, create a feature branch
git checkout -b feature/your-tool

# Set up development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create your tool following the guide in docs/tool-development.md
# Write tests and update documentation

# Commit and push
git commit -m "feat: add new tool"
git push origin feature/your-tool

# Open a pull request
```

## Development

### Running Tests

```bash
# All tests
python -m pytest tests/

# Specific test file
python -m pytest tests/tool-tests.py

# With coverage
python -m pytest --cov=tools tests/
```

### Contributing

1. Create a feature branch
2. Implement your changes with tests
3. Ensure all tests pass
4. Submit a pull request

## Security

- All communication is encrypted
- API keys and tokens are never logged
- OAuth tokens are short-lived and refreshed automatically
- See [Security Guide](./docs/security-guide.md) for details

## Deployment

### Docker
```bash
docker build -t xom-mcp:github tools/github-mcp/
docker run -e GITHUB_TOKEN=$GITHUB_TOKEN xom-mcp:github
```

### Kubernetes
```bash
kubectl apply -f deployment/kubernetes/
```

### Terraform
```bash
cd deployment/terraform/
terraform init
terraform apply
```

## Monitoring

Each MCP server includes:
- Health check endpoints
- Structured logging
- Prometheus metrics
- Error tracking

Access metrics at: `http://localhost:9090/metrics`

## Support

- 📖 [Documentation](./docs/)
- 🐛 [Issues](https://github.com/Xomware/xom-claude-mcp-tools/issues)
- 💬 [Discussions](https://github.com/Xomware/xom-claude-mcp-tools/discussions)

## License

MIT License - see [LICENSE](./LICENSE) file for details

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history.

---

Built with ❤️ by Xomware

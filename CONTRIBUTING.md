# Contributing to xom-claude-mcp-tools

Thank you for your interest in contributing to xom-claude-mcp-tools! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Adding New MCP Tools](#adding-new-mcp-tools)
- [Testing](#testing)
- [Code Style](#code-style)
- [Commit Guidelines](#commit-guidelines)
- [Submitting a Pull Request](#submitting-a-pull-request)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the maintainers.

## Getting Started

1. **Fork the Repository**: Click the "Fork" button on GitHub to create your own copy
2. **Clone Your Fork**: 
   ```bash
   git clone https://github.com/YOUR-USERNAME/xom-claude-mcp-tools.git
   cd xom-claude-mcp-tools
   ```
3. **Add Upstream Remote**:
   ```bash
   git remote add upstream https://github.com/Xomware/xom-claude-mcp-tools.git
   ```

## Development Setup

### Prerequisites

- Python 3.9+
- Git
- pip or poetry
- Docker (optional, for containerized testing)

### Installation

1. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

4. **Verify Installation**:
   ```bash
   python -m pytest tests/ --co -q
   ```

## Making Changes

### Creating a Feature Branch

Always create a new branch for your changes:

```bash
git fetch upstream
git checkout -b feature/your-feature-name upstream/main
```

Branch naming conventions:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

### Updating Your Branch

Keep your branch up to date with upstream:

```bash
git fetch upstream
git rebase upstream/main
```

## Adding New MCP Tools

This is the primary contribution type. Here's the step-by-step process:

### 1. Plan Your Tool

Before starting, consider:

- **Tool Name**: Clear, descriptive, lowercase with hyphens (e.g., `github-mcp`, `slack-mcp`)
- **Purpose**: What service/API does it integrate with?
- **Features**: What tools/operations will it expose?
- **Authentication**: How will it authenticate (API key, OAuth2, token)?

### 2. Create Tool Directory Structure

```bash
mkdir -p tools/YOUR-MCP/tools
touch tools/YOUR-MCP/__init__.py
touch tools/YOUR-MCP/server.py
touch tools/YOUR-MCP/tools/__init__.py
```

### 3. Implement Core Tool Classes

Copy the template and implement your tools:

```bash
cp tools/custom-tools/template.py tools/YOUR-MCP/tools/your_tool.py
```

Example structure:

```python
from typing import Dict, Any, Optional
from loguru import logger

class YourTool:
    """Tool for interacting with YourService."""
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.name = "your_tool"
        self.description = "What this tool does"
    
    async def execute(self, param1: str, param2: int = 10) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        try:
            if not self.validate_inputs(param1, param2):
                return {"error": "Invalid input"}
            
            result = await self._process(param1, param2)
            
            logger.info(f"Tool executed successfully")
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            logger.error(f"Tool error: {e}")
            return {"error": str(e)}
    
    def validate_inputs(self, param1: str, param2: int) -> bool:
        """Validate tool inputs."""
        if not isinstance(param1, str) or not param1:
            return False
        if not isinstance(param2, int) or param2 < 0:
            return False
        return True
    
    async def _process(self, param1: str, param2: int):
        """Internal processing logic."""
        # Implementation here
        return {}
```

### 4. Create the MCP Server

Create `tools/YOUR-MCP/server.py`:

```python
import asyncio
from mcp.server import Server
from mcp.types import Tool
from tools.your_tool import YourTool
from shared.auth import AuthManager

server = Server("your-mcp")
auth_manager = AuthManager()
your_tool = YourTool(auth_manager)

@server.call_tool()
async def handle_tool_call(name: str, arguments: dict):
    """Handle incoming tool calls."""
    if name == "your_tool":
        return await your_tool.execute(**arguments)
    raise ValueError(f"Unknown tool: {name}")

def define_tools():
    """Define MCP tools."""
    return [
        Tool(
            name="your_tool",
            description="Performs your custom operation",
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

if __name__ == "__main__":
    server.set_tools(define_tools())
    asyncio.run(server.run())
```

### 5. Add Authentication (if needed)

If your tool needs authentication, update `shared/auth/` or add to `.env.example`:

```bash
# .env.example
YOUR_SERVICE_API_KEY=your_api_key_here
YOUR_SERVICE_TOKEN=your_token_here
```

### 6. Write Tests

Create `tests/test_your_tool.py`:

```python
import pytest
from tools.YOUR_MCP.tools.your_tool import YourTool

@pytest.fixture
def tool():
    return YourTool(auth_manager=None)

@pytest.mark.asyncio
async def test_execute_success(tool):
    """Test successful execution."""
    result = await tool.execute(param1="test", param2=5)
    assert result["status"] == "success"
    assert result["data"] is not None

@pytest.mark.asyncio
async def test_invalid_input(tool):
    """Test invalid input handling."""
    result = await tool.execute(param1="", param2=-1)
    assert "error" in result

@pytest.mark.asyncio
async def test_validation(tool):
    """Test input validation."""
    assert not tool.validate_inputs("", 5)
    assert not tool.validate_inputs("test", -1)
    assert tool.validate_inputs("test", 5)
```

### 7. Add to Docker Deployment (optional)

Create `deployment/YOUR-MCP.Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "tools/YOUR-MCP/server.py"]
```

Update `deployment/docker-compose.yml` to include your service.

### 8. Document Your Tool

Create `docs/YOUR-MCP.md` with:

```markdown
# YOUR-MCP

Integration with YourService for Claude via MCP.

## Features

- Feature 1
- Feature 2

## Configuration

```bash
YOUR_SERVICE_API_KEY=your_key_here
```

## Usage

```python
# Example usage
```

## Tools

### your_tool
Description and parameters.
```

### 9. Update Main README

Add your tool to the main [README.md](./README.md):

- Add to overview section
- Add to MCP Servers section
- Add to project structure if applicable

## Testing

### Run All Tests

```bash
python -m pytest tests/
```

### Run Specific Tests

```bash
# Single file
python -m pytest tests/test_your_tool.py

# Single test
python -m pytest tests/test_your_tool.py::test_execute_success

# With coverage
python -m pytest --cov=tools tests/
```

### Test Coverage

Aim for >80% code coverage:

```bash
python -m pytest --cov=tools --cov-report=html tests/
```

View results in `htmlcov/index.html`.

### Local Testing with Docker

```bash
cd deployment
docker-compose up -d
# Run integration tests
docker-compose down
```

## Code Style

### Python Style Guide

We follow PEP 8 with Black formatter:

```bash
# Format code
black tools/ tests/

# Check formatting
black --check tools/ tests/

# Sort imports
isort tools/ tests/

# Lint
flake8 tools/ tests/

# Type checking
mypy tools/
```

### Pre-commit Hook (optional)

```bash
# Install hook
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### Code Review Points

- Clear, descriptive variable and function names
- Comprehensive docstrings
- No hardcoded secrets
- Proper error handling
- Comprehensive tests
- Updated documentation

## Commit Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style
- `refactor`: Code refactoring
- `test`: Test improvements
- `chore`: Maintenance

### Examples

```bash
git commit -m "feat(github-mcp): add pr-review tool"
git commit -m "fix(slack-mcp): handle missing user gracefully"
git commit -m "docs: update README with examples"
git commit -m "test: improve database-mcp test coverage"
```

### Sign Commits (recommended)

```bash
git commit -S -m "feat: your message"
```

## Submitting a Pull Request

### Before Submitting

1. **Rebase on latest main**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**:
   ```bash
   python -m pytest tests/
   ```

3. **Check code style**:
   ```bash
   black --check .
   flake8 .
   mypy .
   ```

4. **Update documentation**:
   - Add docstrings
   - Update README if needed
   - Add example usage

### Create Pull Request

1. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open PR on GitHub with:
   - Clear, descriptive title
   - Reference related issues (`Closes #123`)
   - Description of changes
   - Any testing notes

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Breaking change

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests passed
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests passing
- [ ] No new warnings
```

### Review Process

- Address feedback promptly
- Keep commits clean (rebase if needed)
- Don't force push after review starts
- Be respectful and collaborative

## Questions?

- 📖 See [Documentation](./docs/)
- 💬 Open a [Discussion](https://github.com/Xomware/xom-claude-mcp-tools/discussions)
- 🐛 Report [Issues](https://github.com/Xomware/xom-claude-mcp-tools/issues)

## Additional Resources

- [Tool Development Guide](./docs/tool-development.md)
- [MCP Protocol Guide](./docs/mcp-protocol.md)
- [Security Guide](./docs/security-guide.md)
- [Deployment Guide](./docs/deployment.md)

---

Thank you for contributing! 🎉

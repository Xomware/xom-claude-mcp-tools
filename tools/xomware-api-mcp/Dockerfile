FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8004/health')"

# Environment variables
ENV LOG_LEVEL=INFO
ENV SERVER_PORT=8004

# Run server
CMD ["python", "tools/xomware-api-mcp/server.py"]

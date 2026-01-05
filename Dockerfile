FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies and Node.js
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright MCP Server globally (Pinned version for security)
RUN npm install -g @anthropic-ai/mcp-server-playwright@0.1.0

# Install Playwright browsers (needed for the MCP server to function)
RUN npx playwright install --with-deps chromium

# Create restricted non-root user
RUN groupadd -r agent_user && useradd -r -g agent_user -u 10001 agent_user

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY pyproject.toml .
COPY README.md .

# Install the application
RUN pip install .

# Create writable directories for session artifacts
RUN mkdir -p /app/sessions /app/screenshots \
    && chown -R agent_user:agent_user /app

# Switch to non-root user for execution
USER agent_user

# Default command
CMD ["ai-beta-test", "--help"]

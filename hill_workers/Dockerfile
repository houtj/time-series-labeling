# Dockerfile for Hill Workers V1.5
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY uv.lock .
COPY config.py .
COPY database.py .
COPY redis_client.py .
COPY workers/ ./workers/

# Install uv
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Create data folder
RUN mkdir -p /app/data_folder

# Default command (can be overridden)
CMD ["uv", "run", "python", "-m", "workers.file_parser"]


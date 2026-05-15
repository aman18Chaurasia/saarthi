# Dockerfile for SAARTHI API on Google Cloud Run
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy workspace files
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
COPY apps/api/ ./apps/api/

# Install uv
RUN pip install uv

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port (Cloud Run uses PORT env var)
EXPOSE 8080

# Run with uvicorn
CMD uv run uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT}

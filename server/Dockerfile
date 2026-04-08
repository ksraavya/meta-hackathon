FROM python:3.11-slim

WORKDIR /app/env

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir \
    openenv-core==0.2.3 \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    pydantic>=2.0.0 \
    openai>=1.0.0 \
    huggingface-hub>=0.20.0

# Set Python path
ENV PYTHONPATH=/app/env

# Expose port
EXPOSE 8000

# Health check (safe endpoint)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/reset || exit 1

# Run server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
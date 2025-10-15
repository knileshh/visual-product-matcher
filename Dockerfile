# Multi-stage build for optimized image size
# Stage 1: Build stage with all dependencies
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /build

# Install only essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements
COPY requirements.prod.txt requirements.txt

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt && \
    # Remove pip cache and unnecessary files
    rm -rf ~/.cache/pip && \
    find /opt/venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete && \
    find /opt/venv -type f -name "*.pyo" -delete && \
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Stage 2: Runtime stage
FROM python:3.10-slim as runtime

# Set working directory
WORKDIR /app

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/cache/apt/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment to use virtual environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    # Download CLIP model to specific location
    TORCH_HOME=/app/.cache/torch \
    HF_HOME=/app/.cache/huggingface

# Copy only necessary application files
COPY app.py config.yaml ./
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/
COPY deployment/gunicorn_config_cloud.py ./deployment/

# Copy only the necessary data files (embeddings, index, database)
COPY data/embeddings/ ./data/embeddings/
COPY data/index/ ./data/index/
COPY data/products.db ./data/

# Create necessary directories
RUN mkdir -p data/uploads data/temp logs .cache/torch .cache/huggingface && \
    # Set proper permissions
    chmod -R 755 /app

# Expose port
EXPOSE 8080

# Health check (simplified to avoid extra dependencies)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health').read()"

# Run with gunicorn
CMD ["gunicorn", "--config", "deployment/gunicorn_config_cloud.py", "app:create_app()"]

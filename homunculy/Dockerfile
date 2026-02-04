# ===========================================
# Build Stage: Install Dependencies
# ===========================================
FROM python:3.12-slim-bookworm AS builder

LABEL project="homunculy"

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip && \
    pip install --root-user-action=ignore "poetry>=2.1,<2.2"

# Copy dependency files
COPY pyproject.toml poetry.lock /build/

WORKDIR /build

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-cache --only main,db -vv

# ===========================================
# Runtime Stage: Create Lean Image
# ===========================================
FROM python:3.12-slim-bookworm AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security (non-root)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create app directory
WORKDIR $APP_HOME

# Copy application code
COPY --chown=appuser:appuser ./src .

# Copy config files
COPY --chown=appuser:appuser ./config ./config

# Create logs and nltk_data directories
RUN mkdir -p logs /app/nltk_data && chown -R appuser:appuser logs /app/nltk_data

# Switch to non-root user
USER appuser

# Set NLTK data path
ENV NLTK_DATA=/app/nltk_data

# Expose health port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Run worker (default mode)
CMD ["python", "-m", "main"]

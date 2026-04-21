FROM python:3.14-slim AS base
# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
FROM base AS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app/ ./app/
# Install Python deps
RUN pip install --no-cache-dir pip wheel && \
    pip install --no-cache-dir .

# Production image
FROM base AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

COPY --from=deps /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=deps /usr/local/bin/ /usr/local/bin/

# Copy source as a package
COPY app/ ./app/
COPY pyproject.toml ./

# Switch to unprivileged user
USER appuser

# Expose default port
EXPOSE 8000

# Healthcheck: verify the API responds within 3 seconds
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Run via uvicorn (production)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

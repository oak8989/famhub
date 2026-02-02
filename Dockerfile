# =============================================================================
# Family Hub - Self-Hosted Family Organization App
# Multi-stage Docker build for production deployment
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build Frontend
# -----------------------------------------------------------------------------
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies first (better caching)
COPY frontend/package.json frontend/yarn.lock* ./
RUN yarn install --network-timeout 100000

# Copy frontend source
COPY frontend/ ./

# Build with empty backend URL (same-origin in production)
ENV REACT_APP_BACKEND_URL=""
ENV NODE_ENV=production
ENV CI=false

RUN yarn build

# Verify build output
RUN ls -la /app/frontend/build/ && \
    test -f /app/frontend/build/index.html || (echo "Build failed - no index.html" && exit 1)

# -----------------------------------------------------------------------------
# Stage 2: Production Image
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

LABEL org.opencontainers.image.title="Family Hub"
LABEL org.opencontainers.image.description="Self-hosted family organization app"
LABEL org.opencontainers.image.source="https://github.com/oakguy93/family-hub"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy and install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend build from builder stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Verify frontend was copied
RUN ls -la /app/frontend/build/ && \
    test -f /app/frontend/build/index.html || (echo "Frontend build missing" && exit 1)

# Create directories for data persistence
RUN mkdir -p /app/backend/photos /app/data \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables with defaults
ENV MONGO_URL=mongodb://mongo:27017 \
    DB_NAME=family_hub \
    JWT_SECRET=change-this-secret-in-production \
    CORS_ORIGINS=* \
    PORT=8001

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

# Start the application
CMD ["python", "-m", "uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8001"]

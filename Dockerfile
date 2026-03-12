# =============================================================================
# Family Hub - Fully Self-Contained Docker Image
# Single container with MongoDB + FastAPI + React Frontend
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build Frontend
# -----------------------------------------------------------------------------
FROM node:18-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/yarn.lock* ./
RUN yarn install --network-timeout 300000 --ignore-engines

COPY frontend/ ./

ENV REACT_APP_BACKEND_URL=""
ENV NODE_ENV=production
ENV CI=false
ENV DISABLE_ESLINT_PLUGIN=true
ENV GENERATE_SOURCEMAP=false

RUN yarn build
RUN test -f /app/frontend/build/index.html || exit 1

# -----------------------------------------------------------------------------
# Stage 2: Production Image with MongoDB
# -----------------------------------------------------------------------------
FROM ubuntu:22.04

LABEL org.opencontainers.image.title="Family Hub"
LABEL org.opencontainers.image.description="Self-contained family organization app"
LABEL org.opencontainers.image.source="https://github.com/oak8989/family-hub"
LABEL org.opencontainers.image.licenses="MIT"

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    python3 \
    python3-pip \
    python3-venv \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install MongoDB 7.0
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg \
    && echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] http://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" > /etc/apt/sources.list.d/mongodb-org-7.0.list \
    && apt-get update \
    && apt-get install -y mongodb-org \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create Python virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir openai || true

# Copy backend code (modular structure)
COPY backend/ ./backend/

# Copy frontend build
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create directories
RUN mkdir -p /data/db /app/backend/photos /var/log/supervisor

# Create supervisor configuration
RUN echo '[supervisord]\n\
nodaemon=true\n\
user=root\n\
logfile=/var/log/supervisor/supervisord.log\n\
pidfile=/var/run/supervisord.pid\n\
\n\
[program:mongodb]\n\
command=/usr/bin/mongod --bind_ip_all --dbpath /data/db\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/var/log/supervisor/mongodb.log\n\
stderr_logfile=/var/log/supervisor/mongodb_err.log\n\
priority=1\n\
\n\
[program:familyhub]\n\
command=/app/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001\n\
directory=/app/backend\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/var/log/supervisor/familyhub.log\n\
stderr_logfile=/var/log/supervisor/familyhub_err.log\n\
environment=MONGO_URL="%(ENV_MONGO_URL)s",DB_NAME="%(ENV_DB_NAME)s",CORS_ORIGINS="%(ENV_CORS_ORIGINS)s",OPENAI_API_KEY="%(ENV_OPENAI_API_KEY)s",JWT_SECRET="%(ENV_JWT_SECRET)s",SMTP_HOST="%(ENV_SMTP_HOST)s",SMTP_PORT="%(ENV_SMTP_PORT)s",SMTP_USER="%(ENV_SMTP_USER)s",SMTP_PASSWORD="%(ENV_SMTP_PASSWORD)s",SMTP_FROM="%(ENV_SMTP_FROM)s",GOOGLE_CLIENT_ID="%(ENV_GOOGLE_CLIENT_ID)s",GOOGLE_CLIENT_SECRET="%(ENV_GOOGLE_CLIENT_SECRET)s",GOOGLE_REDIRECT_URI="%(ENV_GOOGLE_REDIRECT_URI)s",VAPID_PRIVATE_KEY="%(ENV_VAPID_PRIVATE_KEY)s",VAPID_PUBLIC_KEY="%(ENV_VAPID_PUBLIC_KEY)s",VAPID_EMAIL="%(ENV_VAPID_EMAIL)s",SERVER_URL="%(ENV_SERVER_URL)s"\n\
priority=2\n\
startsecs=5\n\
startretries=3\n\
' > /etc/supervisor/conf.d/familyhub.conf

# Only non-sensitive config as ENV. All secrets (JWT_SECRET, SMTP_PASSWORD,
# OPENAI_API_KEY, GOOGLE_CLIENT_SECRET, VAPID_PRIVATE_KEY) must be passed
# at runtime via: docker run --env-file .env ... or -e KEY=value
ENV MONGO_URL=mongodb://localhost:27017 \
    DB_NAME=family_hub \
    CORS_ORIGINS=* \
    SMTP_HOST="" \
    SMTP_PORT=587 \
    SMTP_USER="" \
    SMTP_FROM="" \
    GOOGLE_CLIENT_ID="" \
    GOOGLE_REDIRECT_URI="" \
    VAPID_PUBLIC_KEY="" \
    VAPID_EMAIL="" \
    SERVER_URL="" \
    PORT=8001

# Expose port (8001 = app)
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/api/health || exit 1

# Volume for data persistence
VOLUME ["/data/db", "/app/backend/photos"]

# Start supervisor (manages both MongoDB and the app)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/familyhub.conf"]

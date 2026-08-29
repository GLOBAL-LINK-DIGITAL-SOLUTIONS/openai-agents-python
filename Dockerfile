# ==============================================================================
# NDLOVU AI / ORA UNIVERSE — OPENAI INTEGRATION DOCKERFILE
# Multi-stage build for OpenAI bridge, chat endpoint, eval registry
# ==============================================================================
# Builder: King Mandingu Letlape
# Base: Python 3.11 Alpine
# Module: F1 Part 4-5 — AI NATION v3.0
# ==============================================================================

FROM python:3.11-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    openssl-dev \
    git

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Runtime Stage
# ==============================================================================

FROM python:3.11-alpine

# Install runtime dependencies only
RUN apk add --no-cache \
    postgresql-client \
    libpq \
    tini

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_ENV=production \
    MANDINGU_VERSION=3.0.0

# Copy application code
COPY openai_bridge.py .
COPY openai_chat_endpoint.py .
COPY model_eval_registry.py .
COPY eval_dataset_builder.py .
COPY openai_custom_provider_config.json .

# Create non-root user for security
RUN addgroup -S mandingu && adduser -S mandingu -G mandingu
USER mandingu

# Expose ports for all services
EXPOSE 8021 8022 8023 8025

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8021/health')" || exit 1

# Use tini as init process
ENTRYPOINT ["/sbin/tini", "--"]

# Default command (can be overridden)
CMD ["uvicorn", "openai_bridge:app", "--host", "0.0.0.0", "--port", "8021"]

# ==============================================================================
# DOCKER BUILD INSTRUCTIONS
# ==============================================================================
# 
# Build for OpenAI Bridge (Container 21):
#   docker build -t ndlovuai/openai-bridge:v3.0.0 \
#     --build-arg SERVICE=openai_bridge \
#     .
#
# Build for OpenAI Chat Endpoint (Container 23):
#   docker build -t ndlovuai/openai-chat-endpoint:v3.0.0 \
#     --build-arg SERVICE=openai_chat_endpoint \
#     .
#
# Build for Model Eval Registry (Container 22):
#   docker build -t ndlovuai/model-eval-registry:v3.0.0 \
#     --build-arg SERVICE=model_eval_registry \
#     .
#
# Build for Eval Dataset Builder (Container 25):
#   docker build -t ndlovuai/eval-dataset-builder:v3.0.0 \
#     --build-arg SERVICE=eval_dataset_builder \
#     .
#
# ==============================================================================
# LABELS FOR CRYTONET & DHARMAKAYA
# ==============================================================================

LABEL \
  org.mandingu.version="3.0.0" \
  org.mandingu.builder="King Mandingu Letlape" \
  org.mandingu.module="F1 Part 4-5" \
  crytonet.tier="critical" \
  crytonet.encryption="aes-256-gcm" \
  dharmakaya.guardian="openai_integration" \
  dharmakaya.zone="sovereign_edge"

# ==============================================================================
# END OF Dockerfile
# ==============================================================================

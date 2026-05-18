# ─────────────────────────────────────────────────────────────
# AVERA — multi-stage Docker build
#
# Stage 1 (builder): install all Python deps into a venv
# Stage 2 (runtime): copy venv + source, run as non-root
#
# Build:
#   docker build -t avera:latest .
#
# Run API server (port 8000):
#   docker run --rm -p 8000:8000 avera:latest
#
# Run CLI analyze on a mounted workspace:
#   docker run --rm \
#     -v /path/to/workspace:/workspace:ro \
#     avera:latest avera analyze \
#       --project /workspace \
#       --out /tmp/reports
#
# Run tests (CI usage):
#   docker run --rm avera:latest pytest
# ─────────────────────────────────────────────────────────────

# ── Stage 1: builder ──────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy only the packaging metadata first (better layer caching)
COPY pyproject.toml ./
COPY src/ ./src/

# Build a wheel and install into an isolated venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir ".[api,dev]"


# ── Stage 2: runtime ─────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="AVERA" \
      org.opencontainers.image.description="AI Change Verification Infrastructure for Safety-Critical Systems" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.licenses="Apache-2.0"

# Non-root user for security
RUN groupadd --gid 1001 avera && \
    useradd --uid 1001 --gid avera --no-create-home --shell /sbin/nologin avera

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source + fixtures (tests need fixture data)
WORKDIR /app
COPY --chown=avera:avera src/ ./src/
COPY --chown=avera:avera tests/ ./tests/
COPY --chown=avera:avera fixtures/ ./fixtures/
COPY --chown=avera:avera pyproject.toml ./

# Install editable (so avera + avera_api are importable)
RUN pip install --no-cache-dir -e ".[api,dev]" --no-build-isolation

USER avera

# Health check — hit the /health endpoint every 30 s
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Default command: start the AVERA API server
CMD ["uvicorn", "avera_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

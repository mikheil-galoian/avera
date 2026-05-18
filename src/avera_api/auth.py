"""API key authentication for the AVERA REST API.

Configuration
-------------
Set the environment variable ``AVERA_API_KEY`` to a secret token before
starting the server:

    export AVERA_API_KEY="your-secret-token"
    uvicorn avera_api.main:app --host 0.0.0.0 --port 8000

    # or via Docker
    docker run -e AVERA_API_KEY=your-secret-token -p 8000:8000 avera:latest

Two header formats are accepted (either one is sufficient):

    X-API-Key: your-secret-token
    Authorization: Bearer your-secret-token

Development mode
----------------
If ``AVERA_API_KEY`` is **not set**, the server starts in open mode and logs a
warning.  This is intentional for local development; never deploy to production
without setting the key.

Token rotation
--------------
To support zero-downtime rotation, set ``AVERA_API_KEY`` to a
comma-separated list of accepted tokens:

    export AVERA_API_KEY="new-token,old-token"

The first token is the canonical current key.  Both are accepted until the
old key is removed from the list.
"""

from __future__ import annotations

import logging
import os
import secrets

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger("avera.auth")

# ── Header extractors ──────────────────────────────────────────────────────────

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer_scheme = HTTPBearer(auto_error=False)

# ── Key loading ────────────────────────────────────────────────────────────────

def _load_keys() -> frozenset[str]:
    """Load accepted API keys from the environment variable.

    Returns an empty frozenset when the variable is not set (open mode).
    """
    raw = os.environ.get("AVERA_API_KEY", "").strip()
    if not raw:
        return frozenset()
    keys = frozenset(k.strip() for k in raw.split(",") if k.strip())
    return keys


def _auth_enabled() -> bool:
    return bool(os.environ.get("AVERA_API_KEY", "").strip())


# ── FastAPI dependency ─────────────────────────────────────────────────────────

async def require_api_key(
    x_api_key: str | None = Security(_api_key_header),
    bearer: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> None:
    """FastAPI dependency — validates the API key on protected routes.

    Raises ``HTTP 401`` when authentication is enabled and no valid key is
    supplied.  When ``AVERA_API_KEY`` is not set, the check is skipped (open
    mode — suitable for local development only).
    """
    if not _auth_enabled():
        logger.warning(
            "AVERA_API_KEY is not set — running in open mode. "
            "Set this variable before deploying to production."
        )
        return

    accepted_keys = _load_keys()

    # Collect the submitted token from either header
    submitted: str | None = None
    if x_api_key:
        submitted = x_api_key
    elif bearer:
        submitted = bearer.credentials

    if submitted is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Supply X-API-Key header or Authorization: Bearer <token>.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Constant-time comparison to prevent timing attacks
    if not any(secrets.compare_digest(submitted, key) for key in accepted_keys):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

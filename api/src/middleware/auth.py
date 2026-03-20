"""
auth.py — API key verification middleware.

Sprint 1: simple env-based key list.
Sprint 2: replace with database-backed key management.
"""

import os
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Sprint 1: load valid keys from environment
# Format in .env: SAUTI_API_KEYS=key1,key2,key3
def _load_valid_keys() -> set[str]:
    raw = os.getenv("SAUTI_API_KEYS", "")
    if not raw:
        # Dev fallback — never use in production
        return {"dev-local-key-do-not-use-in-prod"}
    return set(k.strip() for k in raw.split(",") if k.strip())


VALID_KEYS = _load_valid_keys()


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include X-API-Key header.",
        )
    if api_key not in VALID_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )
    return api_key

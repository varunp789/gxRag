"""HS256 JWT verification and workspace API-key hashing (stdlib only).

Tokens are issued by the deployment's identity provider (or ``issue_token`` for
operators) and signed with ``GXRAG_JWT_SECRET``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from app.core.config import settings

API_KEY_PREFIX = "gxk"


class TokenError(Exception):
    """Raised for any token that must not be trusted."""


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _sign(signing_input: bytes, secret: str) -> str:
    return _b64encode(hmac.new(secret.encode(), signing_input, hashlib.sha256).digest())


def issue_token(subject: str, *, email: str, kind: str = "user", ttl_seconds: int = 3600,
                secret: str | None = None, issuer: str | None = None) -> str:
    secret = secret or settings.jwt_secret
    if not secret:
        raise TokenError("No JWT secret configured.")
    now = int(time.time())
    claims = {"sub": subject, "email": email, "typ": kind, "iss": issuer or settings.jwt_issuer,
              "iat": now, "exp": now + ttl_seconds}
    header = _b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64encode(json.dumps(claims).encode())
    return f"{header}.{body}.{_sign(f'{header}.{body}'.encode(), secret)}"


def decode_token(token: str, *, secret: str | None = None, issuer: str | None = None) -> dict[str, Any]:
    secret = secret or settings.jwt_secret
    if not secret:
        raise TokenError("No JWT secret configured.")
    try:
        header_part, body_part, signature = token.split(".")
        header = json.loads(_b64decode(header_part))
        claims = json.loads(_b64decode(body_part))
    except (ValueError, json.JSONDecodeError) as error:
        raise TokenError("Malformed token.") from error
    # Pin the algorithm: never trust the token's own header to pick one ("alg: none").
    if header.get("alg") != "HS256":
        raise TokenError("Unsupported token algorithm.")
    expected = _sign(f"{header_part}.{body_part}".encode(), secret)
    if not hmac.compare_digest(expected, signature):
        raise TokenError("Invalid token signature.")
    now = time.time()
    leeway = settings.jwt_leeway_seconds
    if not isinstance(claims.get("exp"), (int, float)) or claims["exp"] < now - leeway:
        raise TokenError("Token expired.")
    if isinstance(claims.get("nbf"), (int, float)) and claims["nbf"] > now + leeway:
        raise TokenError("Token not yet valid.")
    if claims.get("iss") != (issuer or settings.jwt_issuer):
        raise TokenError("Unexpected token issuer.")
    if not claims.get("email") or not claims.get("sub"):
        raise TokenError("Token is missing identity claims.")
    return claims


def hash_api_key_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """Return (full_key, prefix, secret_hash). The full key is shown once."""
    prefix = secrets.token_hex(4)
    secret = secrets.token_urlsafe(32)
    return f"{API_KEY_PREFIX}_{prefix}_{secret}", prefix, hash_api_key_secret(secret)


def split_api_key(value: str) -> tuple[str, str] | None:
    parts = value.split("_", 2)
    if len(parts) != 3 or parts[0] != API_KEY_PREFIX:
        return None
    return parts[1], parts[2]


if __name__ == "__main__":  # python -m app.core.security user@example.com [admin]
    import sys

    address = sys.argv[1]
    print(issue_token(address, email=address, kind=sys.argv[2] if len(sys.argv) > 2 else "user"))

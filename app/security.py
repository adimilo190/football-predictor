# app/security.py
# Guard for the admin-only endpoints. The read endpoints of this API are meant to
# be public, but the POST /import-* ones spend our API-Football quota and write to
# the database - once the app is deployed, anybody could trigger them from /docs.
# They are protected by a single shared secret (IMPORT_TOKEN) instead of real user
# accounts, because there is exactly one administrator: the project owner.

import secrets

from fastapi import Header, HTTPException, status

from app.config import settings


def require_import_token(x_import_token: str | None = Header(default=None)) -> None:
    """Reject the request unless it carries the correct X-Import-Token header.

    Used as a FastAPI dependency, so it runs before the endpoint body: raising
    here means the endpoint never executes. FastAPI maps the parameter name
    x_import_token to the HTTP header X-Import-Token (underscores become dashes).
    """
    # "is None" must come first: compare_digest() raises on a None argument, and
    # Python's "or" stops evaluating as soon as the first condition is true.
    #
    # compare_digest() instead of "==" compares in constant time. A plain "=="
    # short-circuits on the first differing character, so the response time would
    # leak how many leading characters an attacker guessed right (a timing attack).
    if x_import_token is None or not secrets.compare_digest(
        x_import_token, settings.IMPORT_TOKEN
    ):
        # 401 = "I do not know who you are" (missing or wrong credentials),
        # as opposed to 403 = "I know who you are, but you may not do this".
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing import token",
        )

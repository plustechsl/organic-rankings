import json
import logging
import urllib.parse
import urllib.request

from fastapi import HTTPException, Request, status

from app.config import (
    TURNSTILE_SECRET_KEY,
    TURNSTILE_TIMEOUT,
    TURNSTILE_VERIFY_URL,
)
from app.net import get_client_ip


logger = logging.getLogger("uvicorn.error")


def turnstile_enabled() -> bool:
    return bool(TURNSTILE_SECRET_KEY)


def verify_turnstile(token: str | None, request: Request) -> None:
    if not turnstile_enabled():
        return

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Captcha verification required",
        )

    payload = urllib.parse.urlencode(
        {
            "secret": TURNSTILE_SECRET_KEY,
            "response": token,
            "remoteip": get_client_ip(request),
        }
    ).encode()

    try:
        with urllib.request.urlopen(
            TURNSTILE_VERIFY_URL,
            data=payload,
            timeout=TURNSTILE_TIMEOUT,
        ) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        logger.warning("Turnstile: fallo al verificar el captcha (%s)", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not verify captcha, please try again",
        )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Captcha verification failed",
        )

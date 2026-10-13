from fastapi import Request

from app.config import TRUSTED_PROXIES


def get_client_ip(request: Request) -> str:
    client_host = request.client.host if request.client else None

    if client_host and client_host in TRUSTED_PROXIES:
        forwarded = request.headers.get("x-forwarded-for")

        if forwarded:
            return forwarded.split(",")[0].strip()

    return client_host or "unknown"

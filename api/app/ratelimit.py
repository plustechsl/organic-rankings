import logging
import time
import uuid

import redis
from fastapi import HTTPException, Request, status

from app.config import (
    CREATION_RATE_LIMIT,
    CREATION_RATE_WINDOW,
    LOGIN_FAIL_LIMIT,
    LOGIN_FAIL_WINDOW,
    LOGIN_RATE_LIMIT,
    LOGIN_RATE_WINDOW,
    RATE_LIMIT_ENABLED,
    REDIS_HOST,
    REDIS_PORT,
    REGISTER_RATE_LIMIT,
    REGISTER_RATE_WINDOW,
    VOTE_IP_RATE_LIMIT,
    VOTE_IP_RATE_WINDOW,
    VOTE_USER_RATE_LIMIT,
    VOTE_USER_RATE_WINDOW,
)
from app.net import get_client_ip
from app.utils import hash_ip


logger = logging.getLogger("uvicorn.error")

_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    global _client

    if _client is None:
        _client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )

    return _client


def _window_hit(key: str, limit: int, window: int) -> int | None:
    if not RATE_LIMIT_ENABLED or limit <= 0:
        return None

    now_ms = int(time.time() * 1000)
    window_ms = window * 1000
    member = f"{now_ms}-{uuid.uuid4().hex}"

    try:
        client = get_client()
        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, now_ms - window_ms)
        pipe.zadd(key, {member: now_ms})
        pipe.expire(key, window)
        pipe.zcard(key)
        _, _, _, count = pipe.execute()
    except redis.RedisError as exc:
        logger.warning("Rate limit: Redis no disponible, se deja pasar (%s)", exc)
        return None

    if count <= limit:
        return None

    try:
        oldest = client.zrange(key, 0, 0, withscores=True)

        if oldest:
            elapsed_ms = now_ms - int(oldest[0][1])
            return max(1, (window_ms - elapsed_ms) // 1000 + 1)
    except redis.RedisError:
        pass

    return window


def _enforce(scope: str, limit: int, window: int, identity: str) -> None:
    retry_after = _window_hit(f"rl:{scope}:{identity}", limit, window)

    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def limit_register(request: Request) -> None:
    _enforce(
        "register",
        REGISTER_RATE_LIMIT,
        REGISTER_RATE_WINDOW,
        f"ip:{hash_ip(get_client_ip(request))}",
    )


def limit_login(request: Request) -> None:
    _enforce(
        "login",
        LOGIN_RATE_LIMIT,
        LOGIN_RATE_WINDOW,
        f"ip:{hash_ip(get_client_ip(request))}",
    )


def limit_vote(request: Request, user_id: int) -> None:
    _enforce(
        "vote",
        VOTE_IP_RATE_LIMIT,
        VOTE_IP_RATE_WINDOW,
        f"ip:{hash_ip(get_client_ip(request))}",
    )
    _enforce(
        "vote",
        VOTE_USER_RATE_LIMIT,
        VOTE_USER_RATE_WINDOW,
        f"user:{user_id}",
    )


def limit_creation(request: Request, user_id: int) -> None:
    _enforce(
        "create",
        CREATION_RATE_LIMIT,
        CREATION_RATE_WINDOW,
        f"user:{user_id}",
    )


def _login_fail_key(username: str) -> str:
    return f"rl:login-fail:{username.strip().lower()}"


def login_locked_retry_after(username: str) -> int | None:
    if not RATE_LIMIT_ENABLED:
        return None

    try:
        client = get_client()
        key = _login_fail_key(username)
        count = client.get(key)

        if count is not None and int(count) >= LOGIN_FAIL_LIMIT:
            ttl = client.ttl(key)
            return max(1, ttl if ttl and ttl > 0 else LOGIN_FAIL_WINDOW)
    except (redis.RedisError, ValueError) as exc:
        logger.warning("Rate limit: Redis no disponible, se deja pasar (%s)", exc)

    return None


def register_login_failure(username: str) -> None:
    if not RATE_LIMIT_ENABLED:
        return

    try:
        client = get_client()
        key = _login_fail_key(username)
        count = client.incr(key)

        if count == 1:
            client.expire(key, LOGIN_FAIL_WINDOW)
    except redis.RedisError as exc:
        logger.warning("Rate limit: Redis no disponible (%s)", exc)


def clear_login_failures(username: str) -> None:
    if not RATE_LIMIT_ENABLED:
        return

    try:
        get_client().delete(_login_fail_key(username))
    except redis.RedisError as exc:
        logger.warning("Rate limit: Redis no disponible (%s)", exc)

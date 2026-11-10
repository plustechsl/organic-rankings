import logging
import threading
import time

import requests

logger = logging.getLogger("uvicorn.error")

GOOGLE_URL = "https://translate.googleapis.com/translate_a/single"
MAX_CHARS = 5000

LANG_MAP = {
    "ca": "ca",
    "en": "en",
    "es": "es",
}

MIN_INTERVAL = 0.3
FAILURE_COOLDOWN = 30.0

_throttle_lock = threading.Lock()
_last_request_at = 0.0
_blocked_until = 0.0


def translation_enabled() -> bool:
    return True


def _acquire_slot() -> bool:
    global _last_request_at

    with _throttle_lock:
        now = time.monotonic()

        if now < _blocked_until:
            return False

        wait = _last_request_at + MIN_INTERVAL - now

        if wait > 0:
            time.sleep(wait)

        _last_request_at = time.monotonic()
        return True


def _block() -> None:
    global _blocked_until

    with _throttle_lock:
        _blocked_until = time.monotonic() + FAILURE_COOLDOWN


def _translate_one(text: str, source: str, target: str) -> str | None:
    if not text or not text.strip():
        return text

    if len(text) > MAX_CHARS:
        return None

    if not _acquire_slot():
        return None

    try:
        response = requests.get(
            GOOGLE_URL,
            params={
                "client": "gtx",
                "sl": source,
                "tl": target,
                "dt": "t",
                "q": text,
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        logger.error("Translation request failed for %r: %s", text, exc)
        return None

    if response.status_code == 429:
        logger.warning("Translation rate limited, pausing")
        _block()
        return None

    if response.status_code != 200:
        logger.error("Translation HTTP %s for %r", response.status_code, text)
        return None

    try:
        segments = response.json()[0]
        translated = "".join(
            segment[0] for segment in segments if segment and segment[0]
        )
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        logger.error("Unexpected translation response for %r: %s", text, exc)
        return None

    return translated.strip() or None


def translate_to_english(text: str) -> str:
    if not text:
        return text

    translated = _translate_one(text, "auto", "en")
    return translated if translated else text


def translate_texts(
    texts: list,
    target_lang: str = None,
    target: str = "en",
    source: str = "auto",
    **kwargs,
) -> list:
    if not texts:
        return texts

    lang = target_lang or target
    lang = LANG_MAP.get(lang, lang)

    return [_translate_one(text or "", source, lang) for text in texts]

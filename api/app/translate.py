import json
import logging
import urllib.error
import urllib.request

from app.config import (
    LIBRETRANSLATE_API_KEY,
    LIBRETRANSLATE_URL,
    TRANSLATE_PROVIDER,
    TRANSLATE_TIMEOUT,
)


logger = logging.getLogger("uvicorn.error")

SUPPORTED_PROVIDERS = {"libretranslate", "none"}

_WARNED_LANGS: set[str] = set()


def _warn_once(target: str, exc: Exception) -> None:
    if target in _WARNED_LANGS:
        return

    _WARNED_LANGS.add(target)
    logger.warning(
        "Translation provider unavailable (target '%s': %s); "
        "serving source text until it recovers",
        target,
        exc,
    )


def translation_enabled() -> bool:
    if TRANSLATE_PROVIDER not in SUPPORTED_PROVIDERS:
        logger.warning(
            "Unknown TRANSLATE_PROVIDER '%s'; translations disabled",
            TRANSLATE_PROVIDER,
        )
        return False

    return TRANSLATE_PROVIDER == "libretranslate"


def translate_texts(
    texts: list[str],
    target: str,
) -> list[str] | None:
    """Traduce un lote de textos al idioma objetivo.

    Devuelve la lista traducida en el mismo orden, o None si el
    proveedor no está disponible (fallo-abierto: el llamante sirve
    el texto original y lo reintenta en la próxima lectura).
    """
    if not texts or not translation_enabled():
        return None

    payload: dict = {
        "q": texts,
        "source": "auto",
        "target": target,
        "format": "text",
    }

    if LIBRETRANSLATE_API_KEY:
        payload["api_key"] = LIBRETRANSLATE_API_KEY

    request = urllib.request.Request(
        f"{LIBRETRANSLATE_URL.rstrip('/')}/translate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=TRANSLATE_TIMEOUT,
        ) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        OSError,
        ValueError,
    ) as exc:
        _warn_once(target, exc)
        return None

    translated = body.get("translatedText")

    if isinstance(translated, list) and len(translated) == len(texts):
        return [str(item) for item in translated]

    if isinstance(translated, str) and len(texts) == 1:
        return [translated]

    logger.warning(
        "Unexpected translation response for target '%s'",
        target,
    )

    return None

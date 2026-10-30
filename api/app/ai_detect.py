import re
import statistics

MIN_WORDS = 150

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")
_WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)?", re.UNICODE)

_STOCK_PHRASES = (
    "en conclusión", "en definitiva", "en resumen", "cabe destacar",
    "es importante destacar", "es fundamental", "en el mundo actual",
    "en la era digital", "un abanico de", "desempeña un papel",
    "no solo", "sin embargo,", "por otro lado", "además,",
    "in conclusion", "it's important to note", "it is important to note",
    "in today's", "fast-paced", "delve", "tapestry", "landscape of",
    "plays a crucial role", "furthermore", "moreover", "game-changer",
    "en conclusió", "és important destacar", "en resum", "cal destacar",
)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _cv(values: list[int]) -> float | None:
    if len(values) < 4:
        return None
    mean = statistics.mean(values)
    if mean == 0:
        return None
    return statistics.pstdev(values) / mean


def analyze_text(text: str) -> dict | None:
    """Estima de 0 a 100 cuánto se parece un texto a contenido generado por IA.

    Devuelve None si el texto es demasiado corto para estimar.
    Es una estimación heurística, no una certificación.
    """
    words = _WORD.findall(text.lower())
    total_words = len(words)
    if total_words < MIN_WORDS:
        return None

    signals: dict[str, tuple[float | None, float]] = {}

    sentences = [s for s in _SENTENCE_SPLIT.split(text) if len(_WORD.findall(s)) >= 3]
    cv = _cv([len(_WORD.findall(s)) for s in sentences])
    signals["frases"] = (None if cv is None else _clamp((0.65 - cv) / 0.35), 0.35)

    lowered = text.lower()
    hits = sum(lowered.count(p) for p in _STOCK_PHRASES)
    density = hits / total_words * 1000
    signals["muletillas"] = (_clamp(density / 4), 0.35)

    paragraphs = [p for p in re.split(r"\n\s*\n|\n", text) if len(_WORD.findall(p)) >= 8]
    pcv = _cv([len(_WORD.findall(p)) for p in paragraphs])
    signals["parrafos"] = (None if pcv is None else _clamp((0.6 - pcv) / 0.4), 0.15)

    trigrams = list(zip(words, words[1:], words[2:]))
    repetition = 1 - len(set(trigrams)) / len(trigrams)
    signals["repeticion"] = (_clamp((repetition - 0.03) / 0.12), 0.15)

    usable = [(v, w) for v, w in signals.values() if v is not None]
    weight_sum = sum(w for _, w in usable)
    score = round(100 * sum(v * w for v, w in usable) / weight_sum)

    if score < 30:
        label = "bajo"
    elif score < 60:
        label = "mixto"
    else:
        label = "alto"

    return {
        "score": score,
        "label": label,
        "words": total_words,
        "confidence": round(min(1.0, total_words / 600), 2),
        "signals": {k: (None if v is None else round(v, 2)) for k, (v, _) in signals.items()},
    }
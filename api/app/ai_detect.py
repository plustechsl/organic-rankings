"""Estima de 0 a 100 cuánto se parece un texto a contenido generado por IA.

Es una estimación aproximada, no un analisis definitivo.
"""

import re
import statistics

# --- Ajustes ----------------------------------------------------------------

MIN_PALABRAS_ANALISIS = 150
PALABRAS_CONFIANZA_TOTAL = 600
MIN_ELEMENTOS_VARIACION = 4
MIN_PALABRAS_FRASE = 3
MIN_PALABRAS_PARRAFO = 8

LIMITE_PUNTUACION_BAJA = 30
LIMITE_PUNTUACION_ALTA = 60

# Peso de cada señal en la puntuación final (suman 1)
PESO_FRASES = 0.35
PESO_MULETILLAS = 0.35
PESO_PARRAFOS = 0.15
PESO_REPETICION = 0.15

SEPARADOR_FRASES = re.compile(r"(?<=[.!?…])\s+")
PATRON_PALABRA = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)?", re.UNICODE)

# Expresiones que la IA repite mucho (es / en / ca)
MULETILLAS = (
    "en conclusión", "en definitiva", "en resumen", "cabe destacar",
    "es importante destacar", "es fundamental", "en el mundo actual",
    "en la era digital", "un abanico de", "desempeña un papel",
    "no solo", "sin embargo,", "por otro lado", "además,",
    "in conclusion", "it's important to note", "it is important to note",
    "in today's", "fast-paced", "delve", "tapestry", "landscape of",
    "plays a crucial role", "furthermore", "moreover", "game-changer",
    "en conclusió", "és important destacar", "en resum", "cal destacar",
)


# --- Funciones auxiliares ---------------------------------------------------

def _contar_palabras(texto: str) -> int:
    return len(PATRON_PALABRA.findall(texto))


def _escalar_entre_0_y_1(valor: float, valor_en_cero: float, valor_en_uno: float) -> float:
    """Devuelve 0 si el valor es `valor_en_cero`, 1 si es `valor_en_uno`,
    y lo proporcional entre medias. Lo que se pase se recorta a 0 o 1."""
    escalado = (valor - valor_en_cero) / (valor_en_uno - valor_en_cero)
    return max(0.0, min(1.0, escalado))


def _variacion_de_longitudes(longitudes: list[int]) -> float | None:
    """Desviación típica entre media. Baja = casi todas miden lo mismo."""
    if len(longitudes) < MIN_ELEMENTOS_VARIACION:
        return None

    media = statistics.mean(longitudes)
    if media == 0:
        return None

    return statistics.pstdev(longitudes) / media


# --- Señales: 0 = parece humano, 1 = parece IA, None = faltan datos ---------

def _senal_frases(texto: str) -> float | None:
    """Frases de longitud muy parecida."""
    frases = [
        frase
        for frase in SEPARADOR_FRASES.split(texto)
        if _contar_palabras(frase) >= MIN_PALABRAS_FRASE
    ]
    variacion = _variacion_de_longitudes([_contar_palabras(f) for f in frases])

    if variacion is None:
        return None

    return _escalar_entre_0_y_1(variacion, valor_en_cero=0.65, valor_en_uno=0.30)


def _senal_muletillas(texto: str, total_palabras: int) -> float:
    """Muletillas típicas de IA por cada 1000 palabras."""
    texto_minusculas = texto.lower()
    total_apariciones = sum(texto_minusculas.count(m) for m in MULETILLAS)
    por_mil_palabras = total_apariciones / total_palabras * 1000

    return _escalar_entre_0_y_1(por_mil_palabras, valor_en_cero=0, valor_en_uno=4)


def _senal_parrafos(texto: str) -> float | None:
    """Párrafos de longitud muy parecida."""
    parrafos = [
        parrafo
        for parrafo in texto.split("\n")
        if _contar_palabras(parrafo) >= MIN_PALABRAS_PARRAFO
    ]
    variacion = _variacion_de_longitudes([_contar_palabras(p) for p in parrafos])

    if variacion is None:
        return None

    return _escalar_entre_0_y_1(variacion, valor_en_cero=0.6, valor_en_uno=0.2)


def _senal_repeticion(palabras: list[str]) -> float:
    """Grupos de tres palabras seguidas que se repiten."""
    trigramas = list(zip(palabras, palabras[1:], palabras[2:]))
    proporcion_repetida = 1 - len(set(trigramas)) / len(trigramas)

    return _escalar_entre_0_y_1(proporcion_repetida, valor_en_cero=0.03, valor_en_uno=0.15)


# --- Resultado  --------------------------------------------------------

def _puntuacion_ponderada(senales_con_peso: list[tuple[float | None, float]]) -> int:
    """Media ponderada de 0 a 100. Las señales sin datos se saltan."""
    disponibles = [(valor, peso) for valor, peso in senales_con_peso if valor is not None]
    peso_total = sum(peso for _, peso in disponibles)
    suma = sum(valor * peso for valor, peso in disponibles)

    return round(100 * suma / peso_total)


def _etiqueta_de_puntuacion(puntuacion: int) -> str:
    if puntuacion < LIMITE_PUNTUACION_BAJA:
        return "bajo"
    if puntuacion < LIMITE_PUNTUACION_ALTA:
        return "mixto"
    return "alto"


def analizar_texto(texto: str) -> dict | None:
    """Analiza el texto. Devuelve None si es demasiado corto.

    Si no, devuelve un diccionario con score (0-100), label, words,
    confidence (0-1) y signals (valor de cada señal).
    """
    palabras = PATRON_PALABRA.findall(texto.lower())
    total_palabras = len(palabras)

    if total_palabras < MIN_PALABRAS_ANALISIS:
        return None

    frases = _senal_frases(texto)
    muletillas = _senal_muletillas(texto, total_palabras)
    parrafos = _senal_parrafos(texto)
    repeticion = _senal_repeticion(palabras)

    puntuacion = _puntuacion_ponderada([
        (frases, PESO_FRASES),
        (muletillas, PESO_MULETILLAS),
        (parrafos, PESO_PARRAFOS),
        (repeticion, PESO_REPETICION),
    ])

    senales = {
        "frases": frases,
        "muletillas": muletillas,
        "parrafos": parrafos,
        "repeticion": repeticion,
    }

    return {
        "score": puntuacion,
        "label": _etiqueta_de_puntuacion(puntuacion),
        "words": total_palabras,
        "confidence": round(min(1.0, total_palabras / PALABRAS_CONFIANZA_TOTAL), 2),
        "signals": {
            nombre: None if valor is None else round(valor, 2)
            for nombre, valor in senales.items()
        },
    }
import re
import unicodedata


ADULT_TERMS = (
    "contenido adulto",
    "contenido para adultos",
    "mayores de 18",
    "porn",
    "porno",
    "pornografia",
    "porno casero",
    "video porno",
    "pelicula porno",
    "xxx",
    "erotico",
    "erotica",
    "erotismo",
    "desnudo",
    "desnuda",
    "desnudez",
    "nudity",
    "nude",
    "nsfw",
    "onlyfans",
    "hentai",
    "milf",
    "camgirl",
    "escort",
    "prostituta",
    "prostibulo",
    "masturbacion",
    "orgasmo",
    "vibrador",
    "consolador",
    "juguetes sexuales",
    "sex shop",
    "fetish",
    "fetiche",
    "bdsm",
    "gangbang",
    "bukkake",
    "creampie",
    "cumshot",
    "sexo explicito",
    "sexo oral",
)

VIOLENCE_TERMS = (
    "violencia",
    "violento",
    "violenta",
    "asesinato",
    "homicidio",
    "tortura",
    "masacre",
    "gore",
    "sangriento",
    "sangrienta",
    "derramamiento de sangre",
    "degollado",
    "degollada",
    "apunalado",
    "apunalada",
    "tiroteo",
    "mutilacion",
    "violacion",
    "abuso sexual",
    "maltrato",
    "genocidio",
    "cadaver",
    "atentado",
    "terrorismo",
    "secuestro",
    "navajazo",
    "ejecucion",
    "escalofriante",
    "perturbador",
    "crueldad",
    "sadismo",
    "golpiza",
    "paliza",
)

LEAD_ADULT_HITS = 1
BODY_ADULT_HITS = 2
LEAD_VIOLENCE_HITS = 1
BODY_VIOLENCE_HITS = 3


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _match_terms(haystack: str, terms: tuple[str, ...]) -> set[str]:
    matched: set[str] = set()

    for term in terms:
        pattern = rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"

        if re.search(pattern, haystack):
            matched.add(term)

    return matched


def detect_sensitivity(
    title: str | None,
    description: str | None,
    text: str | None,
) -> str:
    lead = _normalize(" ".join(part for part in (title, description) if part))
    body = _normalize(text or "")

    adult_lead = _match_terms(lead, ADULT_TERMS)
    adult_body = _match_terms(body, ADULT_TERMS)
    violence_lead = _match_terms(lead, VIOLENCE_TERMS)
    violence_body = _match_terms(body, VIOLENCE_TERMS)

    if (
        len(adult_lead) >= LEAD_ADULT_HITS
        or len(adult_body) >= BODY_ADULT_HITS
    ):
        return "adult"

    if (
        len(violence_lead) >= LEAD_VIOLENCE_HITS
        or len(violence_body) >= BODY_VIOLENCE_HITS
    ):
        return "violence"

    return "none"

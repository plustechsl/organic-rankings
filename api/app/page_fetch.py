import ipaddress
import socket
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

MAX_BYTES = 1_500_000
TIMEOUT = 8
MIN_LINE_WORDS = 6
USER_AGENT = "OrganicRankingsBot/1.0 (+https://www.organicrankings.com)"

_SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "header", "footer", "aside", "form", "iframe"}
_BLOCK_TAGS = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6",
               "section", "article", "tr", "blockquote"}
_ALLOWED_TYPES = {"text/html", "application/xhtml+xml", "text/plain"}


def _assert_public(url: str) -> None:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("URL no válida")

    port = parts.port or (443 if parts.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(parts.hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise ValueError("No se pudo resolver el dominio")

    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not ip.is_global:
            raise ValueError("Dirección no permitida")


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    max_redirections = 3

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _assert_public(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip += 1
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS:
            self._skip = max(0, self._skip - 1)
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


class _MetadataExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            attrs_dict = {key.lower(): (value or "") for key, value in attrs}
            name = (
                attrs_dict.get("property")
                or attrs_dict.get("name")
                or ""
            ).strip().lower()
            content = attrs_dict.get("content", "").strip()

            if name and content and name not in self.meta:
                self.meta[name] = content

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)


def _clean(raw_text: str) -> str:
    lines = (" ".join(line.split()) for line in raw_text.split("\n"))
    return "\n".join(l for l in lines if len(l.split()) >= MIN_LINE_WORDS)


def _fetch_document(url: str) -> tuple[str, str]:
    _assert_public(url)

    opener = urllib.request.build_opener(_SafeRedirect)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain;q=0.9"},
    )

    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            content_type = response.headers.get_content_type()
            if content_type not in _ALLOWED_TYPES:
                raise ValueError("La página no es HTML ni texto")
            raw = response.read(MAX_BYTES)
            charset = response.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        raise ValueError(f"La página respondió {exc.code}")
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ValueError("No se pudo descargar la página")

    try:
        html = raw.decode(charset, errors="replace")
    except LookupError:
        html = raw.decode("utf-8", errors="replace")

    return html, content_type


def fetch_page_text(url: str) -> str:
    """Descarga una página pública y devuelve su texto visible. Lanza ValueError si falla."""
    html, content_type = _fetch_document(url)

    if content_type == "text/plain":
        return _clean(html)

    extractor = _TextExtractor()
    extractor.feed(html)
    return _clean("".join(extractor.parts))


def fetch_page_metadata(url: str) -> dict:
    """Descarga una página pública y devuelve título, descripción y texto visible."""
    html, content_type = _fetch_document(url)

    if content_type == "text/plain":
        lines = [line.strip() for line in html.splitlines() if line.strip()]
        title = lines[0][:200] if lines else ""
        description = " ".join(lines)[:300]
        return {
            "title": title,
            "description": description or None,
            "text": _clean(html),
        }

    extractor = _MetadataExtractor()
    extractor.feed(html)

    text_extractor = _TextExtractor()
    text_extractor.feed(html)

    title = (
        extractor.meta.get("og:title")
        or " ".join(extractor.title_parts).strip()
    )
    description = (
        extractor.meta.get("og:description")
        or extractor.meta.get("description")
    )

    return {
        "title": " ".join(title.split())[:200],
        "description": (
            " ".join(description.split())[:500]
            if description
            else None
        ),
        "text": _clean("".join(text_extractor.parts)),
    }

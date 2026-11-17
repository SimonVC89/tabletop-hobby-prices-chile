"""Cliente HTTP compartido para los scrapers, con reintentos.

Centraliza el User-Agent y la logica de reintento con backoff exponencial,
para que una corrida desatendida (cron) no se caiga entera por un timeout
o un error 5xx puntual de la tienda.
"""

import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


@dataclass(frozen=True)
class PageInfo:
    """Resumen de una pagina descargada, para diagnosticar una tienda que trae 0 productos."""

    url: str
    status: int
    size: int
    title: str | None

    def describe(self) -> str:
        return f"HTTP {self.status}, {self.size} bytes, {self.url}, titulo {self.title!r}"


_last_page: PageInfo | None = None


def last_page() -> PageInfo | None:
    """La ultima pagina que devolvio fetch_html en este proceso (cada tienda corre en el suyo)."""
    return _last_page


def _title(html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return " ".join(match.group(1).split())[:80] if match else None


class StoreClosedError(Exception):
    """La tienda redirige todo a su pagina de contrasena de Shopify (/password).

    Es la forma en que Shopify "cierra" una tienda al publico (vacaciones,
    mantencion): un navegador ve lo mismo, no es un bloqueo al scraper. No se
    reintenta: no es un error pasajero.
    """


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    reraise=True,
)
def fetch_html(url: str, timeout: int = 15) -> str:
    global _last_page
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    _last_page = PageInfo(response.url, response.status_code, len(response.text), _title(response.text))
    if urlparse(response.url).path.rstrip("/") == "/password":
        raise StoreClosedError(f"{url} redirige a {response.url}")
    response.raise_for_status()
    return response.text

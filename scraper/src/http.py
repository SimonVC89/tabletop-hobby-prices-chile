"""Cliente HTTP compartido para los scrapers, con reintentos.

Centraliza el User-Agent y la logica de reintento con backoff exponencial,
para que una corrida desatendida (cron) no se caiga entera por un timeout
o un error 5xx puntual de la tienda.
"""

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    reraise=True,
)
def fetch_html(url: str, timeout: int = 15) -> str:
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text

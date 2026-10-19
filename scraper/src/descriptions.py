"""Extraccion y limpieza de descripciones de producto desde las paginas de las tiendas.

Cada tienda arma su pagina distinto, pero casi todas publican la descripcion
en tres lugares estandar: el JSON-LD del producto, `og:description` y la meta
description. Se prueban en ese orden y se queda el primero que, despues de
limpiar el texto de relleno de la tienda, sigue siendo una descripcion util.

Funciones puras (sin red ni base de datos) para poder probarlas con HTML guardado.
"""

import html
import json
import re
import warnings

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

from src.matching.normalize import strip_accents

# Algunos textos cortos parecen un nombre de archivo o una URL y BeautifulSoup avisa;
# aqui siempre es texto, asi que el aviso no aporta nada.
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

MIN_LENGTH = 60
MAX_LENGTH = 300

# Frases de relleno de tienda (despacho, compra, avisos) que no describen el
# juego. Se descartan por oracion: "El clasico Catan: construye... Envio a todo
# Chile." conserva la primera oracion.
BOILERPLATE = re.compile(
    r"atenci[oó]n|disponible solo online|fecha de env[ií]o|retiros? en tienda|despachos?"
    r"|env[ií]os? (?:a todo|express|gratis|a domicilio)|compra(?:r)? (?:ahora|aqu[ií]|en|tu|juegos|online)"
    r"|tienda online|santiago centro|metro \w+|leer m[aá]s|ver m[aá]s|haz clic|suscr[ií]bete"
    r"|\bstock\b|preventa|pre-venta|cyber|iva incluido|https?://"
    # Avisos legales y de preventa (La Loseta, DeMente): hablan de la compra, no del juego.
    r"|derecho a retracto|no est[aá] sujet[ao]|ley 19\.?496|fecha de llegada"
    r"|precio de venta es estimado|se espera que sea|garant[ií]a|devoluci[oó]n",
    re.IGNORECASE,
)
# Texto alternativo de la imagen ("Portada del juego de mesa 'X' disponible en ...") que
# algunas tiendas usan como descripcion: se descarta entero.
ALT_TEXT = re.compile(r"^(?:portada|imagen|foto|caja) (?:de|del|de la)\b", re.IGNORECASE)
EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿️‍]")
# Listas de piezas ("COMPONENTES 1 libreta, 4 lapices...") en vez de una descripcion.
COMPONENT_LIST = re.compile(r"^(?:componentes|contenido|incluye|contiene)\b", re.IGNORECASE)


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", strip_accents(text).lower())


def _words(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_accents(text).lower()).strip()


def _plain_text(raw: str) -> str:
    """HTML o texto con saltos/tabs -> una sola linea."""
    text = BeautifulSoup(raw, "html.parser").get_text(" ")
    text = EMOJI.sub("", html.unescape(text)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _truncate(text: str) -> str:
    if len(text) <= MAX_LENGTH:
        return text
    window = text[:MAX_LENGTH]
    end = max(window.rfind(". "), window.rfind("! "), window.rfind("? "), window.rfind("."))
    if end >= 120:  # cortar en una oracion completa si no se pierde demasiado
        return window[: end + 1]
    return window[: window.rfind(" ")].rstrip(" ,;:-–—") + "…"


def clean_description(raw: str | None, title: str, store_name: str | None = None) -> str | None:
    """Devuelve la descripcion lista para mostrar, o None si no sirve."""
    if not raw:
        return None

    brand = _squash(store_name) if store_name else None
    sentences = re.split(r"(?<=[.!?…])\s+", _plain_text(raw))
    kept = [
        s for s in sentences
        if s and not BOILERPLATE.search(s) and not (brand and len(brand) >= 5 and brand in _squash(s))
    ]
    text = " ".join(kept).strip(" -–—|")
    if len(text) < MIN_LENGTH or COMPONENT_LIST.match(text) or ALT_TEXT.match(text):
        return None

    # Titulo repetido (con o sin un par de palabras: "Dominations - Español").
    plain, plain_title = _words(text), _words(title)
    if plain_title and plain.startswith(plain_title) and len(plain) < len(plain_title) + 25:
        return None

    return _truncate(text)


def _json_ld_descriptions(soup: BeautifulSoup) -> list[str]:
    found = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except ValueError:
            continue
        for item in data if isinstance(data, list) else [data]:
            nodes = item.get("@graph", [item]) if isinstance(item, dict) else []
            for node in nodes:
                kind = node.get("@type") if isinstance(node, dict) else None
                is_product = kind == "Product" or (isinstance(kind, list) and "Product" in kind)
                if is_product and isinstance(node.get("description"), str):
                    found.append(node["description"])
    return found


def candidate_texts(page_html: str) -> list[str]:
    """Textos candidatos de una pagina, del mas al menos confiable."""
    soup = BeautifulSoup(page_html, "html.parser")
    candidates = _json_ld_descriptions(soup)
    for attrs in ({"property": "og:description"}, {"name": "description"}):
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            candidates.append(tag["content"])
    return candidates


def best_description(page_html: str, title: str, store_name: str) -> str | None:
    for raw in candidate_texts(page_html):
        cleaned = clean_description(raw, title, store_name)
        if cleaned:
            return cleaned
    return None

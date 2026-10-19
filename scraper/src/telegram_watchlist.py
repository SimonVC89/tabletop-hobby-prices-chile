"""Seguimiento de juegos por Telegram: comandos (/seguir, /siguiendo, /dejar) y avisos.

El bot no tiene servidor (ver poll_telegram_commands): cada comando se resuelve
sin estado entre mensajes. Por eso /seguir responde con opciones que son
comandos tocables (/seguir_c827edbb), en vez de esperar un "elige el 2", y la
paginacion lleva la busqueda dentro del comando (/mas_2_arkham_horror_lcg).

Busqueda (no hay autocompletado real: Telegram solo lo permite con "modo inline",
que exige un servidor que responda en segundos):
- cada palabra escrita es un prefijo ("nav" encuentra "Navegantes"), sin importar
  tildes, mayusculas ni orden;
- entiende sinonimos ("exp", "ampliacion" y "expansion" son lo mismo);
- si no encuentra nada, corrige errores de tipeo ("catna" -> "catan");
- si hay mas de MAX_OPTIONS resultados, sugiere palabras para acotar y permite
  paginar.

Avisos (los manda send_telegram_digest tras cada corrida de scraping):
- el mejor precio con stock baja al menos WATCH_DROP_PCT% bajo el nivel de
  referencia (el precio al seguir o el de la ultima vez que se aviso);
- un juego que estaba agotado vuelve a tener stock.
No se avisa cuando el precio sube ni cuando se agota; el nivel de referencia solo
se mueve en los avisos, asi dos bajadas chicas seguidas no se pierden.
"""

import re
from collections import Counter
from difflib import get_close_matches

from src.matching.normalize import canonical, strip_accents

MAX_FOLLOWS = 20
MAX_OPTIONS = 5
WATCH_DROP_PCT = 5
CODE_LENGTH = 8  # primeros caracteres del id del producto; ver code_of
# Telegram solo convierte en enlace un comando corto; si la busqueda no cabe, no se ofrece "ver mas".
MAX_COMMAND_LENGTH = 60
# Una palabra muy corta no se corrige: "ark" podria ser cualquier cosa.
MIN_CORRECTABLE_LENGTH = 4
TYPO_CUTOFF = 0.75

# Palabras que no ayudan a acotar una busqueda: conectores y "juego"/"mesa", que estan en casi todo.
STOPWORDS = {
    "de", "del", "la", "el", "los", "las", "y", "en", "con", "para", "un", "una", "the", "of", "and", "por",
    "al", "lo", "juego", "mesa",
}
# Como mostrar al usuario las palabras que son sinonimos canonicos (sin tilde en la clave).
DISPLAY = {"expansion": "expansión", "edicion": "edición", "jugadores": "jugadores"}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_accents(text).lower()).strip()


def code_of(product_id: str) -> str:
    """Codigo corto y tocable del producto: la primera parte de su UUID."""
    return str(product_id)[:CODE_LENGTH]


def clp(value: int) -> str:
    return "$" + f"{value:,}".replace(",", ".")


# --- busqueda: logica pura (se prueba sin base de datos) -------------------

def _forms(token: str) -> tuple[str, ...]:
    """El token y, si es un sinonimo, su forma canonica ("ampliacion" -> tambien "expansion")."""
    canon = canonical(token)
    return (token,) if canon == token else (token, canon)


def _term_matches(term: str, token_forms: list[tuple[str, ...]]) -> bool:
    """Una palabra escrita encaja si es prefijo de alguna palabra del nombre (o de su sinonimo)."""
    wanted = _forms(term)
    return any(form.startswith(w) for forms in token_forms for form in forms for w in wanted)


def match_catalog(catalog: list[dict], terms: list[str]) -> list[dict]:
    """Juegos del catalogo que contienen todas las palabras (como prefijos), ordenados.

    Primero el nombre exacto, luego los que tienen stock, luego los nombres mas
    cortos (el juego base antes que sus expansiones) y los mas comparables.
    """
    exact = " ".join(terms)
    matches = [item for item in catalog if all(_term_matches(t, item["forms"]) for t in terms)]
    for item in matches:
        item["exact"] = item["normalized"] == exact
    matches.sort(key=lambda m: (not m["exact"], m["price"] is None, len(m["name"]), -m["stores"]))
    return matches


def correct_terms(catalog: list[dict], terms: list[str]) -> list[str]:
    """Reemplaza las palabras que no existen en ningun nombre por la mas parecida.

    Solo corrige palabras de MIN_CORRECTABLE_LENGTH o mas. Devuelve las mismas
    palabras si no hay nada que corregir.
    """
    vocabulary = Counter(tok for item in catalog for forms in item["forms"] for tok in forms[:1])
    corrected = []
    for term in terms:
        known = any(tok.startswith(t) for tok in vocabulary for t in _forms(term))
        if known or len(term) < MIN_CORRECTABLE_LENGTH:
            corrected.append(term)
            continue
        close = get_close_matches(term, vocabulary, n=1, cutoff=TYPO_CUTOFF)
        corrected.append(close[0] if close else term)
    return corrected


def narrowing_words(matches: list[dict], terms: list[str], limit: int = 5) -> list[str]:
    """Palabras que mejor separan los resultados: presentes en varios pero no en todos.

    Sirven para decirle a la persona que agregar a la busqueda ("campaña",
    "investigadores"...) en vez de dejarla adivinando entre decenas de nombres.
    """
    total = len(matches)
    asked = {f for t in terms for f in _forms(t)}
    counts, shown = Counter(), {}
    for item in matches:
        seen = set()
        for original in re.findall(r"[^\W_]+", item["name"]):
            token = _norm(original)
            if not token or token in STOPWORDS or len(token) < 4 or token.isdigit():
                continue
            key = canonical(token)
            if key in seen or any(key.startswith(a) or token.startswith(a) for a in asked):
                continue
            seen.add(key)
            counts[key] += 1
            # Se muestra la forma con tilde si algun nombre la trae ("campaña", no "campana").
            candidate = DISPLAY.get(key) or original.lower()
            if key not in shown or _accents(candidate) > _accents(shown[key]):
                shown[key] = candidate
    scored = [(min(c, total - c), key) for key, c in counts.items() if 2 <= c < total]
    scored.sort(key=lambda s: (-s[0], len(s[1]), s[1]))

    chosen: list[str] = []
    for _, key in scored:
        # Singular y plural son la misma pista ("investigador" / "investigadores").
        if any(key.startswith(other) or other.startswith(key) for other in chosen):
            continue
        chosen.append(key)
        if len(chosen) == limit:
            break
    return [shown[key] for key in chosen]


def _accents(text: str) -> int:
    """Cuantas letras con tilde o ñ tiene un texto (para preferir la forma bien escrita)."""
    return sum(1 for ch in text if ch not in strip_accents(ch))


def more_command(page: int, terms: list[str]) -> str | None:
    """Comando tocable para ver otra pagina, o None si la busqueda no cabe en un comando."""
    command = f"/mas_{page}_" + "_".join(terms)
    return command if len(command) <= MAX_COMMAND_LENGTH else None


def parse_more_command(rest: str) -> tuple[int, list[str]] | None:
    """'2_arkham_horror_lcg' -> (2, ['arkham', 'horror', 'lcg']); None si no es valido."""
    page, _, query = rest.partition("_")
    terms = [t for t in query.split("_") if t]
    if not page.isdigit() or int(page) < 2 or not terms:
        return None
    return int(page), terms


# --- busqueda: acceso a la base ------------------------------------------

def _load_catalog(conn) -> list[dict]:
    """Juegos visibles con su mejor precio con stock, listos para buscar."""
    with conn.cursor() as cur:
        cur.execute(
            """
            select p.id::text, p.canonical_name, coalesce(pps.store_count, 0), b.min_price
            from products p
            left join product_price_stats pps on pps.product_id = p.id
            left join (
                select product_id, min(price_clp) as min_price
                from current_prices where in_stock group by product_id
            ) b on b.product_id = p.id
            where p.hidden_at is null and p.merged_into is null and p.category = 'board_game'
            """
        )
        rows = cur.fetchall()
    catalog = []
    for pid, name, store_count, min_price in rows:
        normalized = _norm(name)
        catalog.append({
            "id": pid, "name": name, "stores": store_count, "price": min_price,
            "normalized": normalized, "forms": [_forms(tok) for tok in normalized.split()],
        })
    return catalog


def search(conn, query: str) -> dict:
    """Busca juegos por nombre. Devuelve {"matches", "terms", "corrected"}.

    "corrected" es la busqueda corregida si hubo que arreglar errores de tipeo
    (y solo entonces), para poder decirle a la persona "¿quisiste decir…?".
    """
    terms = _norm(query).split()
    if not terms:
        return {"matches": [], "terms": [], "corrected": None}

    catalog = _load_catalog(conn)
    matches = match_catalog(catalog, terms)
    corrected = None
    if not matches:
        fixed = correct_terms(catalog, terms)
        if fixed != terms:
            matches = match_catalog(catalog, fixed)
            if matches:
                terms, corrected = fixed, " ".join(fixed)
    return {"matches": matches, "terms": terms, "corrected": corrected}


def search_products(conn, query: str) -> list[dict]:
    return search(conn, query)["matches"]


def best_offer(conn, product_id: str):
    """(precio, tienda, url) del mejor precio con stock del producto, o None."""
    with conn.cursor() as cur:
        cur.execute(
            """
            select cp.price_clp, s.name, pl.url
            from current_prices cp
            join stores s on s.id = cp.store_id
            join product_listings pl on pl.id = cp.listing_id
            where cp.product_id = %s and cp.in_stock
            order by cp.price_clp limit 1
            """,
            (product_id,),
        )
        return cur.fetchone()


# --- comandos -------------------------------------------------------------

def _chat_state(conn, chat_id: str):
    """Registra el chat si es nuevo (sin suscribirlo al resumen) y devuelve (baja_total, bloqueado)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into telegram_subscribers (chat_id, is_active, last_command_at)
            values (%s, false, now())
            on conflict (chat_id) do update set last_command_at = now()
            returning opted_out_permanently, is_blocked
            """,
            (chat_id,),
        )
        return cur.fetchone()


def _refuse_if_opted_out(opted_out: bool, blocked: bool):
    if blocked:
        return ""  # no se responde a chats bloqueados
    if opted_out:
        return (
            "Te diste de baja total anteriormente, así que no puedo seguir juegos para ti. "
            "Para volver necesitas hacerlo desde la página web (todavía no está disponible)."
        )
    return None


def _options(matches: list[dict]) -> str:
    lines = []
    for m in matches:
        price = f"desde {clp(m['price'])}" if m["price"] is not None else "agotado"
        lines.append(f"\n{m['name']} ({price})\n/seguir_{code_of(m['id'])}")
    return "\n".join(lines)


def _footer(matches: list[dict], terms: list[str], page: int, hints: bool) -> str:
    """Pie de la lista: cuantos hay, como ver mas y que palabras agregar para acotar."""
    total = len(matches)
    start = (page - 1) * MAX_OPTIONS
    shown_to = min(start + MAX_OPTIONS, total)
    if total <= MAX_OPTIONS:
        return ""

    parts = [f"\nMostrando {start + 1}-{shown_to} de {total}."]
    if shown_to < total:
        link = more_command(page + 1, terms)
        if link:
            parts.append(f"Ver los siguientes: {link}")
    if hints:
        words = narrowing_words(matches, terms)
        if words:
            parts.append("Para acotar, agrega una palabra: " + ", ".join(words))
    return "\n".join(parts)


def handle_seguir(conn, chat_id: str, query: str) -> str | None:
    opted_out, blocked = _chat_state(conn, chat_id)
    refusal = _refuse_if_opted_out(opted_out, blocked)
    if refusal is not None:
        return refusal or None

    query = query.strip()
    if not query:
        return (
            "Dime qué juego quieres seguir, por ejemplo:\n/seguir catan\n\n"
            "Te aviso cuando baje de precio o vuelva a tener stock."
        )

    found = search(conn, query)
    matches, terms, corrected = found["matches"], found["terms"], found["corrected"]
    if not matches:
        return f"No encontré juegos con «{query}». Prueba con menos palabras o revisa cómo se escribe."
    # Con un error de tipeo corregido se pide confirmar, aunque haya una sola coincidencia.
    if len(matches) == 1 and not corrected:
        return _follow(conn, chat_id, matches[0]["id"], matches[0]["name"])

    if corrected:
        header = f"No encontré «{query}». ¿Quisiste decir «{corrected}»? Toca el juego que quieres seguir:"
    else:
        header = f"Encontré {len(matches)} juegos con «{query}». Toca el que quieres seguir:"
    return header + "\n" + _options(matches[:MAX_OPTIONS]) + "\n" + _footer(matches, terms, 1, hints=True)


def handle_mas(conn, chat_id: str, rest: str) -> str | None:
    """Otra pagina de resultados: /mas_<pagina>_<palabras separadas por _>."""
    opted_out, blocked = _chat_state(conn, chat_id)
    refusal = _refuse_if_opted_out(opted_out, blocked)
    if refusal is not None:
        return refusal or None

    parsed = parse_more_command(rest)
    if not parsed:
        return "Ese comando no es válido. Usa /seguir seguido del nombre del juego."
    page, terms = parsed

    matches = match_catalog(_load_catalog(conn), terms)
    start = (page - 1) * MAX_OPTIONS
    if start >= len(matches):
        return "No hay más resultados para esa búsqueda."

    query = " ".join(terms)
    header = f"Juegos con «{query}»: {start + 1}-{min(start + MAX_OPTIONS, len(matches))} de {len(matches)}. Toca el que quieres seguir:"
    return header + "\n" + _options(matches[start:start + MAX_OPTIONS]) + "\n" + _footer(matches, terms, page, hints=False)


def handle_seguir_code(conn, chat_id: str, code: str) -> str | None:
    opted_out, blocked = _chat_state(conn, chat_id)
    refusal = _refuse_if_opted_out(opted_out, blocked)
    if refusal is not None:
        return refusal or None

    product = _product_by_code(conn, code)
    if isinstance(product, str):
        return product
    return _follow(conn, chat_id, product["id"], product["name"])


def _product_by_code(conn, code: str):
    """Producto visible por su codigo, o un texto de error para el usuario."""
    if not re.fullmatch(r"[0-9a-f]{%d}" % CODE_LENGTH, code):
        return "Ese código no es válido. Usa /seguir seguido del nombre del juego."
    with conn.cursor() as cur:
        cur.execute(
            """
            select id::text, canonical_name from products
            where id::text like %s and hidden_at is null and merged_into is null and category = 'board_game'
            """,
            (code + "%",),
        )
        rows = cur.fetchall()
    if len(rows) != 1:
        return "No encontré ese juego (puede que ya no esté disponible). Busca de nuevo con /seguir y el nombre."
    return {"id": rows[0][0], "name": rows[0][1]}


def _follow(conn, chat_id: str, product_id: str, name: str) -> str:
    with conn.cursor() as cur:
        cur.execute("select count(*) from telegram_watchlist where chat_id = %s", (chat_id,))
        total = cur.fetchone()[0]
        cur.execute("select 1 from telegram_watchlist where chat_id = %s and product_id = %s", (chat_id, product_id))
        already = cur.fetchone() is not None

        if already:
            return f"Ya sigues {name}. Mira tu lista con /siguiendo."
        if total >= MAX_FOLLOWS:
            return (
                f"Ya sigues {MAX_FOLLOWS} juegos, que es el máximo. "
                "Deja de seguir alguno con /siguiendo para agregar otro."
            )

        offer = best_offer(conn, product_id)
        cur.execute(
            "insert into telegram_watchlist (chat_id, product_id, ref_price, in_stock) values (%s, %s, %s, %s)",
            (chat_id, product_id, offer[0] if offer else None, offer is not None),
        )

    if offer:
        status = f"Hoy el mejor precio es {clp(offer[0])} en {offer[1]}."
        promise = f"Te aviso cuando baje al menos {WATCH_DROP_PCT}% más o si se agota y vuelve."
    else:
        status = "Hoy está agotado en las tiendas que sigo."
        promise = "Te aviso cuando vuelva a tener stock."
    return f"⭐ Ahora sigues {name}.\n{status} {promise}\nVe tu lista con /siguiendo."


def handle_siguiendo(conn, chat_id: str) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            select p.id::text, p.canonical_name, b.min_price
            from telegram_watchlist w
            join products p on p.id = w.product_id
            left join (
                select product_id, min(price_clp) as min_price
                from current_prices where in_stock group by product_id
            ) b on b.product_id = w.product_id
            where w.chat_id = %s
            order by w.created_at
            """,
            (chat_id,),
        )
        rows = cur.fetchall()

    if not rows:
        return "Todavía no sigues ningún juego. Prueba con /seguir y el nombre, por ejemplo: /seguir catan"

    lines = [f"Sigues {len(rows)} de {MAX_FOLLOWS} juegos posibles:"]
    for pid, name, price in rows:
        status = clp(price) if price is not None else "agotado"
        lines.append(f"\n{name} ({status})\nDejar de seguir: /dejar_{code_of(pid)}")
    return "\n".join(lines)


def handle_dejar_code(conn, chat_id: str, code: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{%d}" % CODE_LENGTH, code):
        return "Ese código no es válido. Mira tu lista con /siguiendo."
    with conn.cursor() as cur:
        cur.execute(
            """
            delete from telegram_watchlist w using products p
            where w.product_id = p.id and w.chat_id = %s and p.id::text like %s
            returning p.canonical_name
            """,
            (chat_id, code + "%"),
        )
        row = cur.fetchone()
    if not row:
        return "No estabas siguiendo ese juego. Mira tu lista con /siguiendo."
    return f"Listo, dejé de seguir {row[0]}."


# --- avisos ---------------------------------------------------------------

def decide(prev_in_stock: bool, ref_price: int | None, best: int | None) -> tuple[str | None, int | None, bool]:
    """Que pasa con un juego seguido en esta revision.

    Devuelve (evento, nuevo nivel de referencia, nuevo estado de stock). El evento
    es "restock", "drop" o None. Ver el docstring del modulo para las reglas.
    """
    if best is None:
        return None, ref_price, False  # se agoto: sin aviso, se recuerda para detectar el regreso
    if not prev_in_stock or ref_price is None:
        return "restock", best, True
    if best <= ref_price * (1 - WATCH_DROP_PCT / 100):
        return "drop", best, True
    return None, ref_price, True


def collect_alerts(conn) -> tuple[list[dict], list[dict]]:
    """Revisa todos los juegos seguidos. Devuelve (avisos, cambios silenciosos).

    Un aviso lleva el estado nuevo (new_ref / new_in_stock) que solo debe guardarse
    cuando el mensaje se envio bien; un cambio silencioso (se agoto) se guarda ya.
    Solo considera chats que pueden recibir mensajes (sin baja total ni bloqueo).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            select w.chat_id, w.product_id::text, p.canonical_name, w.ref_price, w.in_stock,
                   b.price_clp, b.store_name, b.url
            from telegram_watchlist w
            join telegram_subscribers t on t.chat_id = w.chat_id
            join products p on p.id = w.product_id
            left join lateral (
                select cp.price_clp, s.name as store_name, pl.url
                from current_prices cp
                join stores s on s.id = cp.store_id
                join product_listings pl on pl.id = cp.listing_id
                where cp.product_id = w.product_id and cp.in_stock
                order by cp.price_clp limit 1
            ) b on true
            where not t.opted_out_permanently and not t.is_blocked
            """
        )
        rows = cur.fetchall()

    alerts, silent = [], []
    for chat_id, product_id, name, ref_price, in_stock, best, store, url in rows:
        event, new_ref, new_in_stock = decide(in_stock, ref_price, best)
        if event:
            alerts.append({
                "chat_id": chat_id, "product_id": product_id, "name": name, "event": event,
                "price": best, "previous": ref_price, "store": store, "url": url,
                "new_ref": new_ref, "new_in_stock": new_in_stock,
            })
        elif (new_ref, new_in_stock) != (ref_price, in_stock):
            silent.append({"chat_id": chat_id, "product_id": product_id, "new_ref": new_ref, "new_in_stock": new_in_stock})
    return alerts, silent


def save_state(conn, changes: list[dict], alerted: bool):
    with conn.cursor() as cur:
        for c in changes:
            cur.execute(
                """
                update telegram_watchlist
                set ref_price = %s, in_stock = %s, last_alert_at = case when %s then now() else last_alert_at end
                where chat_id = %s and product_id = %s
                """,
                (c["new_ref"], c["new_in_stock"], alerted, c["chat_id"], c["product_id"]),
            )


def format_watch_section(alerts: list[dict]) -> str:
    lines = ["⭐ De tu lista:"]
    for a in alerts:
        if a["event"] == "drop":
            drop = round(100 * (a["previous"] - a["price"]) / a["previous"])
            what = f"bajó a {clp(a['price'])} en {a['store']} (antes {clp(a['previous'])}, -{drop}%)"
        else:
            what = f"volvió a tener stock desde {clp(a['price'])} en {a['store']}"
        lines.append(f"• {a['name']} {what}\n  {a['url']}")
    return "\n".join(lines)

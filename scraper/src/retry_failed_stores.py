"""Reintenta las tiendas cuyo scraper fallo en la corrida del cron.

Cada tienda es un step con continue-on-error en .github/workflows/scraper.yml. Si el
sitio de una tienda se cae unos minutos, los reintentos por pagina (src/http.py,
segundos) no alcanzan; aqui se vuelve a correr la tienda completa despues de esperar,
cuando las demas ya terminaron, asi nadie mas se atrasa. Reintentar es seguro: los
listings se actualizan y price_history solo guarda cambios.

El workflow pasa el resultado de cada step en STORE_OUTCOMES, una linea por tienda:
    src.ingest_laloseta=failure
    src.ingest_dementegames=success

Una tienda que sigue fallando despues de los reintentos es solo una advertencia si es
la primera corrida que falla: una caida o un bloqueo pasajero (La Loseta a veces no
acepta conexiones desde los runners de GitHub) no hace perder nada, porque sus listings
siguen activos hasta STALE_AFTER_DAYS. Si tampoco se pudo leer en la corrida anterior,
es un error y el script sale con codigo 1 (el job queda fallido y GitHub avisa por email).
"""

import importlib
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

from src.db import get_connection

# Espera antes de cada reintento: el sitio tiene tiempo de recuperarse.
WAITS_SECONDS = (120, 300)
# Entre corridas hay 10 o 14 h (05:17 y 19:17): sin leerse bien en 20 h significa que
# fallo esta corrida y tambien la anterior.
REPEATED_FAILURE_AFTER = timedelta(hours=20)


def parse_outcomes(text: str) -> dict[str, str]:
    """'src.ingest_x=failure' por linea -> {'src.ingest_x': 'failure'}."""
    outcomes = {}
    for line in text.splitlines():
        module, sep, outcome = line.strip().partition("=")
        if sep and module:
            outcomes[module.strip()] = outcome.strip()
    return outcomes


def run_store(module: str) -> bool:
    return subprocess.run([sys.executable, "-m", module]).returncode == 0


def retry_failed(outcomes: dict[str, str], run=run_store, sleep=time.sleep,
                 waits: tuple[int, ...] = WAITS_SECONDS) -> list[str]:
    """Reintenta las tiendas que no terminaron bien. Devuelve las que siguen fallando."""
    pending = [m for m, outcome in outcomes.items() if outcome != "success"]
    for attempt, wait in enumerate(waits, start=1):
        if not pending:
            break
        print(f"Reintento {attempt} de {len(waits)} en {wait} s: {', '.join(pending)}", flush=True)
        sleep(wait)
        pending = [m for m in pending if not run(m)]
    return pending


def repeated_failures(modules: list[str], last_seen: dict[str, datetime | None], now: datetime) -> list[str]:
    """Las que tampoco se leyeron bien en la corrida anterior. Sin dato cuenta como repetida."""
    return [m for m in modules
            if last_seen.get(m) is None or now - last_seen[m] > REPEATED_FAILURE_AFTER]


def last_seen_in_db(modules: list[str]) -> dict[str, datetime | None]:
    """Ultima vez que cada tienda se leyo bien: el last_seen_at mas reciente de sus listings."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            seen = {}
            for module in modules:
                # Cada src.ingest_* define el nombre de su tienda.
                store = importlib.import_module(module).STORE_NAME
                cur.execute(
                    "select max(pl.last_seen_at) from stores s "
                    "join product_listings pl on pl.store_id = s.id where s.name = %s",
                    (store,),
                )
                seen[module] = cur.fetchone()[0]
            return seen
    finally:
        conn.close()


def main():
    outcomes = parse_outcomes(os.environ.get("STORE_OUTCOMES", ""))
    failed = [m for m, o in outcomes.items() if o != "success"]
    if not failed:
        print("Todas las tiendas terminaron bien en el primer intento.")
        return
    still_failing = retry_failed(outcomes)
    try:
        last_seen = last_seen_in_db(still_failing) if still_failing else {}
    except Exception as e:
        # Sin saber cuando se leyo cada una, se marca error: mejor un aviso de mas que uno de menos.
        print(f"No se pudo consultar la ultima lectura de las tiendas ({e}); se marcan como error.")
        last_seen = {}
    repeated = repeated_failures(still_failing, last_seen, datetime.now(timezone.utc))
    tries = len(WAITS_SECONDS)
    for module in failed:
        # Anotaciones visibles en el resumen de la corrida en GitHub.
        if module in repeated:
            print(f"::error::{module} sigue fallando despues de {tries} reintentos y tampoco se leyo "
                  f"en la corrida anterior")
        elif module in still_failing:
            print(f"::warning::{module} sigue fallando despues de {tries} reintentos; es la primera "
                  f"corrida que falla, si falla tambien la proxima se marca como error")
        else:
            print(f"::notice::{module} fallo en el primer intento y se recupero al reintentar")
    if repeated:
        sys.exit(1)


if __name__ == "__main__":
    main()

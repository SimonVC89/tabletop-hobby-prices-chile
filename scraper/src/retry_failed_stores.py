"""Reintenta las tiendas cuyo scraper fallo en la corrida del cron.

Cada tienda es un step con continue-on-error en .github/workflows/scraper.yml. Si el
sitio de una tienda se cae unos minutos, los reintentos por pagina (src/http.py,
segundos) no alcanzan; aqui se vuelve a correr la tienda completa despues de esperar,
cuando las demas ya terminaron, asi nadie mas se atrasa. Reintentar es seguro: los
listings se actualizan y price_history solo guarda cambios.

El workflow pasa el resultado de cada step en STORE_OUTCOMES, una linea por tienda:
    src.ingest_laloseta=failure
    src.ingest_dementegames=success

Sale con codigo 1 si alguna tienda sigue fallando despues de los reintentos.
"""

import os
import subprocess
import sys
import time

# Espera antes de cada reintento: el sitio tiene tiempo de recuperarse.
WAITS_SECONDS = (120, 300)


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


def main():
    outcomes = parse_outcomes(os.environ.get("STORE_OUTCOMES", ""))
    failed = [m for m, o in outcomes.items() if o != "success"]
    if not failed:
        print("Todas las tiendas terminaron bien en el primer intento.")
        return
    still_failing = retry_failed(outcomes)
    for module in failed:
        if module in still_failing:
            # Anotacion visible en el resumen de la corrida en GitHub.
            print(f"::error::{module} sigue fallando despues de {len(WAITS_SECONDS)} reintentos")
        else:
            print(f"::notice::{module} fallo en el primer intento y se recupero al reintentar")
    if still_failing:
        sys.exit(1)


if __name__ == "__main__":
    main()

# Tabletop Hobby Prices Chile

Monitoreo de precios de juegos de mesa en tiendas chilenas online. El objetivo
es detectar ofertas reales por **asimetría de información** entre tiendas
(una tienda que no actualiza su precio según la referencia real de mercado),
no errores de tipeo puntuales.

## Motivación

Proyecto personal, nacido de una colección de +50 juegos de mesa y las ganas
de automatizar algo que hacía manualmente (comparar precios entre tiendas
antes de comprar). Es open source para que otros aficionados al hobby en
Chile puedan revisarlo, usarlo o adaptarlo a su propio stack.

## Stack

| Capa | Tecnología |
|---|---|
| Scraping | Python (Requests + BeautifulSoup) |
| Matching de productos | Normalización determinística + embeddings (sentence-transformers, local) |
| Base de datos | Supabase (Postgres + pgvector) |
| Automatización | GitHub Actions (cron) |
| Backend | Spring Boot (Java), desplegado en Render |
| Frontend | React + TypeScript + Vite, desplegado en Vercel |
| Alertas | Bot de Telegram |

Todo corre en capas gratuitas — es un proyecto de uso personal, no un
servicio comercial.

## Arquitectura

```
scrapers (Python) --> Supabase (Postgres + pgvector)
                           |
                           v
                  matching (match_key determinístico
                   + embeddings como capa secundaria)
                           |
                           v
                  backend API (Spring Boot, Render)
                      /          \
                     v            v
         frontend (React, Vercel)   alertas (Telegram)
```

El scraper se conecta directo a Postgres (no vía la Data API de Supabase):
las tablas quedaron deliberadamente sin exponer por REST, así que tanto el
scraper como el backend hablan directo con la base, como dos servicios
internos — no hay superficie pública adicional que proteger.

## Estado actual

- Esquema de datos completo: `stores`, `products`, `product_listings`,
  `price_history`, `price_alerts`, con soporte pgvector.
- 10 scrapers de tiendas chilenas funcionando: La Loseta, DeMente Games,
  UpDown, VuduGaming, Griffin Games, Aldea Juegos, Mana House, Café 2d6,
  El Patio Geek, Wargaming. (PlanetaLoz fue parte del proyecto hasta
  octubre de 2026, ver "Scraping responsable".)
- Pipeline de matching: clave determinística (`match_key`) como mecanismo
  principal, embeddings (Hugging Face / sentence-transformers) como capa
  secundaria de revisión.
- ~11.700 listings scrapeados, ~2.350 productos comparables entre 2 o más
  tiendas. Cada producto tiene imagen y descripción corta, extraídas del
  propio HTML scrapeado (sin depender de ninguna API externa).
- Cron diario corriendo en GitHub Actions para 9 de las 10 tiendas (UpDown
  queda solo para corrida manual, ver "Scraping responsable").
- Bot de Telegram funcionando (`/start`, `/stop`, `/dar_de_baja`, `/ayuda`):
  resumen diario de ofertas (destacadas 50%+ y regulares 20%+ bajo la
  mediana), con polling cada ~15 min vía GitHub Actions.
- Política de retención de datos: `price_history` se poda a 8 meses, y un
  producto sin ningún listing activo hace 6+ meses se oculta (soft-delete,
  reversible si vuelve a aparecer).
- Alcance actual: solo juegos de mesa modernos. El soporte para Magic: The
  Gathering (singles y producto sellado) está diseñado en el esquema pero
  pausado por ahora.

## Roadmap

- [ ] Dockerización (scraper + backend) con `docker-compose` para desarrollo local
- [ ] Tests (`pytest` para el scraper/matching, JUnit para el backend)
- [ ] Logging estructurado (reemplazar `print()`)
- [ ] Validación de datos con Pydantic en el scraper
- [x] Reintentos con backoff exponencial en requests HTTP
- [x] CI/CD con GitHub Actions: cron diario de scraping + matching
- [x] Vistas materializadas (`current_prices`, `product_price_stats`) con
      precio de referencia por mediana entre tiendas, refrescadas en cada
      corrida del cron
- [x] Bot de Telegram con resumen diario de ofertas, suscripción abierta y
      polling de comandos (sin servidor persistente, ver memoria del proyecto)
- [x] Política de retención: poda de `price_history` (8 meses) y soft-delete
      de productos descontinuados (6 meses sin listings activos)
- [ ] CI/CD por carpeta para `backend/` y `frontend/` (tests/build en PRs)
- [ ] Backend: API REST con DTOs, paginación, cache y documentación OpenAPI/Swagger
- [ ] Frontend con gráficos de precio histórico (Recharts)
- [ ] Sub-categorización de juegos de mesa (familiar/estrategia/party, etc.) —
      cada tienda usa su propia taxonomía, sin estándar compartido entre ellas
- [ ] Reactivar MTG (singles vía Scryfall, sellado vía matching propio)

## Scraping responsable

- Delay de 1.5s entre requests a la misma tienda.
- Las tiendas con protección activa anti-bot (Cloudflare, etc.) se excluyen
  deliberadamente en vez de intentar evadir la protección.
- **UpDown no corre en el cron automático**: devuelve 403 Forbidden
  específicamente desde las IPs de los runners de GitHub Actions (bloqueo a
  tráfico de datacenter), aunque funciona sin problema corrida manualmente
  desde una red residencial. Por la misma razón de arriba, no se intenta
  sortear ese bloqueo — su script de ingesta sigue disponible para correr
  en local. **Efecto secundario conocido**: como la política de retención
  marca un listing inactivo si no se ve en 3+ días, sus precios quedan
  afuera de la comparación poco después de cada corrida manual, y un
  producto exclusivo de UpDown podría ocultarse como "descontinuado" a los
  6 meses sin corrida — no porque haya desaparecido, sino por falta de
  monitoreo. Correrla manualmente cada tanto evita esto; se aceptó el
  riesgo en vez de agregar un umbral de retención distinto por tienda.
- **PlanetaLoz fue excluida (octubre de 2026)**: empezó a bloquear todo
  acceso automatizado (403 incluso desde una conexión residencial, mientras
  que un navegador normal entra sin problema). Se respetó el bloqueo: se
  eliminó su scraper, la tienda quedó marcada inactiva y su historial de
  precios hasta septiembre se conserva. Si la tienda lo autoriza, el código
  sigue disponible en el historial de git.
- Uso estrictamente personal y no comercial.

## Licencia

MIT — ver [LICENSE](LICENSE).

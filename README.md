# Tabletop Hobby Prices Chile

[![CI scraper](https://github.com/SimonVC89/tabletop-hobby-prices-chile/actions/workflows/ci-scraper.yml/badge.svg?branch=main)](https://github.com/SimonVC89/tabletop-hobby-prices-chile/actions/workflows/ci-scraper.yml)
[![CI backend](https://github.com/SimonVC89/tabletop-hobby-prices-chile/actions/workflows/ci-backend.yml/badge.svg?branch=main)](https://github.com/SimonVC89/tabletop-hobby-prices-chile/actions/workflows/ci-backend.yml)
[![CI frontend](https://github.com/SimonVC89/tabletop-hobby-prices-chile/actions/workflows/ci-frontend.yml/badge.svg?branch=main)](https://github.com/SimonVC89/tabletop-hobby-prices-chile/actions/workflows/ci-frontend.yml)
[![Licencia MIT](https://img.shields.io/github/license/SimonVC89/tabletop-hobby-prices-chile)](LICENSE)

Monitoreo de precios de juegos de mesa en tiendas chilenas online. El objetivo
es detectar ofertas reales por **asimetría de información** entre tiendas
(una tienda que no actualiza su precio según la referencia real de mercado),
no errores de tipeo puntuales.

**Sitio:** https://thpc.vercel.app · **API (documentación y pruebas con Swagger):** https://thpc-api.onrender.com/swagger-ui.html

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
| Automatización | GitHub Actions, lanzado a la hora exacta por cron-job.org |
| Backend | Spring Boot (Java), desplegado en Render |
| Frontend | React + TypeScript + Vite, desplegado en Vercel |
| Alertas | Bot de Telegram |

Todo corre en capas gratuitas — es un proyecto de uso personal, no un
servicio comercial.

## Arquitectura

```
GitHub Actions (05:17 y 19:17, lanzado por cron-job.org)
  scrapers + matching (Python) --escribe--> Supabase (Postgres + pgvector)
  resumen y avisos (Telegram)  <--lee-----/        |
                                                   | lee (usuario de solo lectura)
                                                   v
                                  API REST (Spring Boot, Docker en Render)
                                         |                    ^
                                         v                    | webhook (comandos del bot)
                             frontend (React, Vercel)      Telegram
```

El scraper se conecta directo a Postgres (no vía la Data API de Supabase):
las tablas quedaron deliberadamente sin exponer por REST, así que tanto el
scraper como el backend hablan directo con la base, como dos servicios
internos — no hay superficie pública adicional que proteger. La API usa un
rol propio (`thpc_api`) que solo puede leer las tablas que necesita: si sus
credenciales se filtraran, no servirían para modificar ni borrar datos.

## Estado actual

- Esquema de datos completo: `stores`, `products`, `product_listings`,
  `price_history`, `price_alerts`, con soporte pgvector.
- 13 scrapers de tiendas chilenas funcionando: La Loseta, DeMente Games,
  UpDown, VuduGaming, Griffin Games, Aldea Juegos, Mana House, Café 2d6,
  El Patio Geek, Wargaming, Diverti, Piedra Bruja y Jugones. (PlanetaLoz
  fue parte del proyecto hasta octubre de 2026, ver "Scraping responsable".)
- Clasificación de productos: lo que las tiendas listan como "juegos de
  mesa" pero no lo es (protectores, boosters de TCG, naipes, libros de rol,
  puzzles) se clasifica aparte y queda fuera de ofertas, alertas y frontend.
  Los complementos de un juego específico (expansiones, dados o insertos
  propios) sí cuentan como juego de mesa.
- Pipeline de matching: clave determinística (`match_key`) como mecanismo
  principal, embeddings (Hugging Face / sentence-transformers) como capa
  secundaria (hoy alimentan "juegos similares"). El nombre visible de cada
  producto se elige por votación entre tiendas (el título que más tiendas
  escriben igual, limpio de sufijos como " - Español").
- ~3.000 juegos de mesa comprables hoy, ~1.060 comparables en 2+ tiendas
  (con stock) y ~570 con mediana confiable (3+ tiendas). Cada producto tiene imagen y descripción corta, extraídas del
  propio HTML scrapeado (sin depender de ninguna API externa).
- Dos corridas diarias en GitHub Actions (05:17 y 19:17, justo después del
  horario laboral) para 12 de las 13 tiendas; UpDown queda solo para corrida
  manual, ver "Scraping responsable". Las lanza cron-job.org a la hora exacta
  vía la API de GitHub: el `schedule` propio de GitHub las arrancaba con 3 a 7
  horas de atraso. El historial de precios guarda solo cambios.
- Bot de Telegram (`/start`, `/stop`, `/seguir`, `/siguiendo`, `/dar_de_baja`,
  `/ayuda`): resumen de ofertas (destacadas 50%+ y regulares 20%+ bajo la
  mediana) y avisos de los juegos que cada persona sigue (bajan de precio o
  vuelven a tener stock). Los comandos llegan por webhook a la API, que responde
  en segundos (antes se leían con un workflow programado que en la práctica
  corría cada ~3 horas); el resumen y los avisos salen desde Python después de
  cada corrida del scraper.
- API REST en Spring Boot 4 (Java 21) con el mismo contrato que consume el
  frontend (`frontend/src/api/types.ts`): ofertas, búsqueda paginada,
  ficha, historial diario reconstruido y juegos relacionados (similitud de
  pgvector). Publicada en Render con Docker; un ping periódico evita que el
  plan gratuito la duerma. Documentada con OpenAPI (springdoc): en
  `/swagger-ui.html` se ven todos los endpoints y se pueden probar.
- Frontend en React publicado en Vercel: Inicio, ofertas, buscador, ficha
  con gráfico de historial por tienda, página del bot y "Cómo funciona".
- Política de retención de datos: `price_history` se poda a 8 meses, y un
  producto sin ningún listing activo hace 6+ meses se oculta (soft-delete,
  reversible si vuelve a aparecer).
- Alcance actual: solo juegos de mesa modernos. El soporte para Magic: The
  Gathering (singles y producto sellado) está diseñado en el esquema pero
  pausado por ahora.

## Roadmap

- [x] Imagen Docker del backend (con CDS para arrancar rápido en el plan gratuito)
- [ ] `docker-compose` para levantar todo en local
- [x] Tests (`pytest` para el scraper/matching, JUnit para el backend)
- [ ] Logging estructurado (reemplazar `print()`)
- [ ] Validación de datos con Pydantic en el scraper
- [x] Reintentos con backoff exponencial en requests HTTP
- [x] CI/CD con GitHub Actions: cron diario de scraping + matching
- [x] Vistas materializadas (`current_prices`, `product_price_stats`) con
      precio de referencia por mediana entre tiendas, refrescadas en cada
      corrida del cron
- [x] Bot de Telegram con resumen diario de ofertas, suscripción abierta y
      polling de comandos (sin servidor persistente)
- [x] Webhook de Telegram en el backend, para que el bot responda en segundos
- [x] Política de retención: poda de `price_history` (8 meses) y soft-delete
      de productos descontinuados (6 meses sin listings activos)
- [x] CI por carpeta para `scraper/`, `backend/` y `frontend/` en cada push y PR: pytest, JUnit + build del backend, lint + build del frontend
- [x] Backend: API REST con DTOs, paginación y caché del catálogo
- [x] Documentación OpenAPI/Swagger de la API
- [x] Frontend con gráficos de precio histórico (Recharts)
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

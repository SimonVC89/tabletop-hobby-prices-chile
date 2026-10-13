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
- 11 scrapers de tiendas chilenas funcionando: La Loseta, DeMente Games,
  UpDown, VuduGaming, PlanetaLoz, Griffin Games, Aldea Juegos, Mana House,
  Café 2d6, El Patio Geek, Wargaming.
- Pipeline de matching: clave determinística (`match_key`) como mecanismo
  principal, embeddings (Hugging Face / sentence-transformers) como capa
  secundaria de revisión.
- ~11.600 listings scrapeados, ~2.300 productos comparables entre 2 o más
  tiendas.
- Alcance actual: solo juegos de mesa modernos. El soporte para Magic: The
  Gathering (singles y producto sellado) está diseñado en el esquema pero
  pausado por ahora.

## Roadmap

- [ ] Dockerización (scraper + backend) con `docker-compose` para desarrollo local
- [ ] Tests (`pytest` para el scraper/matching, JUnit para el backend)
- [ ] Logging estructurado (reemplazar `print()`)
- [ ] Validación de datos con Pydantic en el scraper
- [ ] Reintentos con backoff exponencial en requests HTTP
- [ ] CI/CD con GitHub Actions, separado por carpeta (`scraper/`, `backend/`, `frontend/`)
- [ ] Backend: API REST con DTOs, paginación, cache y documentación OpenAPI/Swagger
- [ ] Vista materializada de "precio actual" para no recalcular en cada request
- [ ] Precio de referencia por mediana móvil + alertas automáticas vía Telegram
- [ ] Frontend con gráficos de precio histórico (Recharts)
- [ ] Reactivar MTG (singles vía Scryfall, sellado vía matching propio)

## Scraping responsable

- Delay de 1.5s entre requests a la misma tienda.
- Las tiendas con protección activa anti-bot (Cloudflare, etc.) se excluyen
  deliberadamente en vez de intentar evadir la protección.
- **UpDown y PlanetaLoz no corren en el cron automático**: ambas devuelven
  403 Forbidden específicamente desde las IPs de los runners de GitHub
  Actions (probablemente un bloqueo a tráfico de datacenter o fuera de
  Chile), aunque funcionan sin problema corridas manualmente desde una red
  residencial. Por la misma razón de arriba, no se intenta sortear ese
  bloqueo — sus scripts de ingesta siguen disponibles para correr en local.
- Uso estrictamente personal y no comercial.

## Licencia

MIT — ver [LICENSE](LICENSE).

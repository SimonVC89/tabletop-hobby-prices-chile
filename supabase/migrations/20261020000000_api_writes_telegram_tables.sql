-- El bot de Telegram pasa a responder desde la API (webhook), asi que thpc_api
-- necesita escribir en las tablas del bot: suscribir, seguir y dejar de seguir
-- juegos, y recordar el ultimo mensaje procesado.
--
-- Los permisos por tabla siguen siendo la barrera real: el catalogo de precios
-- (stores, products, product_listings, price_history y las vistas) sigue siendo
-- solo SELECT. Se quita el "solo lectura por defecto" de la migracion anterior,
-- que bloqueaba toda escritura sin distinguir tablas; las lecturas de la API
-- siguen corriendo en transacciones de solo lectura (@Transactional(readOnly = true)).

alter role thpc_api reset default_transaction_read_only;

grant select, insert, update on telegram_subscribers to thpc_api;
grant select, insert, delete on telegram_watchlist to thpc_api;
-- last_update_id: evita procesar dos veces un mensaje que Telegram reenvia.
grant select, insert, update on telegram_bot_state to thpc_api;

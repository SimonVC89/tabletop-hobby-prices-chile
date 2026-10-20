-- Rol de solo lectura para la API REST (backend Spring Boot publicado en Render).
-- La API solo lee: si sus credenciales se filtraran, no servirian para borrar ni
-- modificar datos. El scraper sigue usando su propio usuario.
--
-- La clave NO va en el repositorio: se asigna aparte con
--   alter role thpc_api password '...';
-- y se guarda en backend/.env (local) y en las variables de entorno de Render.
-- Por el pooler de Supabase el usuario se escribe "thpc_api.<id del proyecto>".

create role thpc_api with login noinherit nocreatedb nocreaterole;

-- Defensa extra: toda transaccion es de solo lectura aunque se pidiera escribir,
-- una consulta no puede pasar de 15 s y el rol no acapara las conexiones del plan.
alter role thpc_api set default_transaction_read_only = on;
alter role thpc_api set statement_timeout = '15s';
alter role thpc_api connection limit 10;

grant usage on schema public to thpc_api;

-- Exactamente lo que lee la API (ver backend/src/main/java/.../*Queries.java).
grant select on
  stores,
  products,
  product_listings,
  price_history,
  current_prices,
  product_price_stats
to thpc_api;

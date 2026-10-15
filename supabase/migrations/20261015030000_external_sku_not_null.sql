-- external_sku es la identidad de un listing dentro de su tienda (junto
-- con store_id). Si llega NULL, la restriccion UNIQUE no lo detecta
-- (NULL <> NULL en Postgres) y el upsert inserta una fila nueva en cada
-- corrida: paso con UpDown, cuyos productos agotados no tenian SKU.
-- Con NOT NULL, un scraper que vuelva a fallar asi revienta en vez de
-- duplicar datos en silencio.
alter table product_listings alter column external_sku set not null;

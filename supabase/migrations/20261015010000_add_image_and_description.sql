-- image_url vive en product_listings (viaja del scraper al momento del
-- match) y tambien en products (ya existia, es la copia "elegida" para
-- mostrar). description es nueva en ambas tablas: viene del atributo alt
-- de la imagen en la pagina de categoria de cada tienda (no hay fuente
-- externa, ver memoria del proyecto sobre descartar BoardGameGeek).
alter table product_listings add column image_url text;
alter table product_listings add column description text;
alter table products add column description text;

-- Las descripciones reales viven en la pagina de cada producto, no en la
-- grilla del catalogo que leen los scrapers diarios (que solo trae el titulo
-- repetido). fetch_descriptions las busca una vez por producto.

-- Tienda de la que salio products.description, para mostrar la fuente.
alter table products add column description_source text;

-- Cuando se reviso la pagina de este listing. Evita volver a pedirla y deja
-- que una nueva corrida pruebe con la siguiente tienda si esta no sirvio.
alter table product_listings add column description_checked_at timestamptz;

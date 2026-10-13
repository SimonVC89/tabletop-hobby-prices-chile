-- Clave determinista de matching: titulo normalizado y con palabras
-- ordenadas alfabeticamente, para agrupar el mismo producto entre tiendas
-- sin depender solo de similitud difusa de embeddings.
alter table product_listings add column match_key text;
alter table products add column match_key text;

create index idx_product_listings_match_key on product_listings(match_key);
create index idx_products_match_key on products(match_key);

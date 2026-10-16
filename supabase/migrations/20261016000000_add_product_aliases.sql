-- Fusion de productos duplicados (el mismo juego partido en varios porque
-- cada tienda lo nombra distinto: "Catan" / "Catan Basico" / "Catan El Juego").

-- Claves de matching que corresponden a otro producto. assign_products las
-- consulta antes que products.match_key, asi un listing nuevo con una clave
-- ya fusionada se une solo al producto correcto.
create table product_aliases (
  match_key text primary key,
  product_id uuid not null references products(id) on delete cascade,
  created_at timestamptz not null default now()
);

-- Un producto absorbido no se borra: queda oculto (hidden_at) y apuntando al
-- que lo absorbio. Sus listings pasan al principal, pero conservan su
-- match_key, asi que la fusion se puede deshacer.
alter table products add column merged_into uuid references products(id);
create index idx_products_merged_into on products(merged_into) where merged_into is not null;

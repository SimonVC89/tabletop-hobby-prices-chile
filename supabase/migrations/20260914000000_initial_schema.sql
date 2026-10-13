-- Extensiones necesarias
create extension if not exists pgcrypto;   -- gen_random_uuid()
create extension if not exists vector;     -- pgvector, para el matching por embeddings

-- Enums
create type product_category as enum ('board_game', 'mtg_single', 'mtg_sealed');
create type mtg_finish as enum ('nonfoil', 'foil', 'etched');
create type mtg_sealed_type as enum ('bundle', 'commander_deck', 'booster_box', 'collector_booster_box', 'other');
create type card_condition as enum ('NM', 'LP', 'MP', 'HP', 'DMG');

-- Tiendas scrapeadas
create table stores (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  base_url text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

-- Producto canonico (independiente de tienda)
create table products (
  id uuid primary key default gen_random_uuid(),
  category product_category not null,
  canonical_name text not null,
  image_url text,
  scryfall_id uuid,              -- solo mtg_single: identifica el printing exacto
  finish mtg_finish,             -- solo mtg_single
  set_code text,                 -- mtg_single y mtg_sealed
  sealed_type mtg_sealed_type,   -- solo mtg_sealed
  created_at timestamptz not null default now()
);

-- Listado concreto de un producto en una tienda especifica
create table product_listings (
  id uuid primary key default gen_random_uuid(),
  product_id uuid references products(id),   -- nullable hasta que el matching lo asigne
  store_id uuid not null references stores(id),
  raw_title text not null,
  url text not null,
  external_sku text,
  condition card_condition,      -- solo mtg_single
  language text,                 -- ESP/ENG/etc, aplica a board_game y mtg_single
  title_embedding vector(384),   -- dimension segun el modelo de HF que usemos
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  is_active boolean not null default true
);

-- Historico de precios por listing
create table price_history (
  id bigserial primary key,
  listing_id uuid not null references product_listings(id),
  price_clp integer not null,
  in_stock boolean not null default true,
  scraped_at timestamptz not null default now()
);

-- Cache de precios de referencia de Scryfall (solo mtg_single)
create table mtg_reference_prices (
  scryfall_id uuid primary key,
  price_usd numeric,
  price_usd_foil numeric,
  price_usd_etched numeric,
  fetched_at timestamptz not null default now()
);

-- Alertas de oferta enviadas
create table price_alerts (
  id uuid primary key default gen_random_uuid(),
  listing_id uuid not null references product_listings(id),
  price_clp integer not null,
  reference_price_clp integer not null,
  discount_pct numeric not null,
  notified_at timestamptz not null default now()
);

-- Indices de soporte
create index idx_product_listings_product_id on product_listings(product_id);
create index idx_product_listings_store_id on product_listings(store_id);
create index idx_price_history_listing_id on price_history(listing_id);
create index idx_products_category on products(category);

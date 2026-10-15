-- Soft-delete de productos descontinuados (sin listings activos hace
-- meses). NULL = visible; con fecha = oculto desde ese momento.
alter table products add column hidden_at timestamptz;

-- current_prices debe ignorar listings inactivos (los que ya no se ven
-- en el scraping hace dias): si no, un listing muerto queda "congelado"
-- para siempre con su ultimo precio conocido, distorsionando la mediana.
drop materialized view product_price_stats;
drop materialized view current_prices;

create materialized view current_prices as
select distinct on (pl.id)
  pl.id as listing_id,
  pl.product_id,
  pl.store_id,
  ph.price_clp,
  ph.in_stock,
  ph.scraped_at
from product_listings pl
join price_history ph on ph.listing_id = pl.id
where pl.is_active
order by pl.id, ph.scraped_at desc;

create unique index idx_current_prices_listing_id on current_prices (listing_id);
create index idx_current_prices_product_id on current_prices (product_id);

create materialized view product_price_stats as
select
  product_id,
  count(distinct store_id) as store_count,
  percentile_cont(0.5) within group (order by price_clp) as median_price_clp,
  min(price_clp) as min_price_clp,
  max(price_clp) as max_price_clp
from current_prices
where in_stock
group by product_id;

create unique index idx_product_price_stats_product_id on product_price_stats (product_id);

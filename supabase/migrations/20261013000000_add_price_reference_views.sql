-- Precio actual de cada listing: la fila mas reciente de price_history.
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
order by pl.id, ph.scraped_at desc;

create unique index idx_current_prices_listing_id on current_prices (listing_id);
create index idx_current_prices_product_id on current_prices (product_id);

-- Mediana de precio por producto, solo con listings en stock.
-- store_count queda expuesto para que quien consulte decida el minimo de
-- tiendas que exige antes de confiar en la mediana (hoy: 3, ver README).
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

-- La mediana se calculaba sobre listings: si una tienda publica el mismo
-- juego en dos paginas, su precio pesaba doble (y podia inflar el descuento
-- de otra tienda). Ahora cada tienda aporta un solo precio: el mas bajo que
-- tenga con stock. Mismas columnas, asi que los consumidores no cambian.
drop materialized view product_price_stats;

create materialized view product_price_stats as
with per_store as (
  select product_id, store_id, min(price_clp) as price_clp
  from current_prices
  where in_stock
  group by product_id, store_id
)
select
  product_id,
  count(*) as store_count,
  percentile_cont(0.5) within group (order by price_clp) as median_price_clp,
  min(price_clp) as min_price_clp,
  max(price_clp) as max_price_clp
from per_store
group by product_id;

create unique index idx_product_price_stats_product_id on product_price_stats (product_id);

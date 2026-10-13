-- Evita duplicados cuando el scraper corre repetidamente (cron diario).
alter table stores
  add constraint stores_name_key unique (name);

alter table product_listings
  add constraint product_listings_store_sku_key unique (store_id, external_sku);

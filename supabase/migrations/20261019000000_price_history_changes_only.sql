-- price_history pasa a registrar solo CAMBIOS de precio o stock (ver
-- db.insert_price_history). Para saber si algo cambio hay que mirar la ultima
-- fila de cada listing: este indice la encuentra directo, y reemplaza al de
-- listing_id solo, que queda cubierto por el prefijo.
create index idx_price_history_listing_scraped on price_history (listing_id, scraped_at desc);
drop index idx_price_history_listing_id;

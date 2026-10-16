-- El nombre de la tienda lleva tilde. upsert_store busca por nombre, asi
-- que el renombre tiene que estar aplicado antes de que corra el scraper
-- con el nombre nuevo (si no, crearia una tienda duplicada).
update stores set name = 'Café 2d6' where name = 'Cafe 2d6';

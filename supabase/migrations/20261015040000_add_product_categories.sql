-- Categorias para lo que las tiendas listan como "juegos de mesa" pero no
-- lo es. No se borran: se clasifican (src/matching/classify.py) y los
-- consumidores (ofertas, Telegram, frontend) filtran por 'board_game'.
alter type product_category add value if not exists 'accessory';
alter type product_category add value if not exists 'tcg';
alter type product_category add value if not exists 'rpg';
alter type product_category add value if not exists 'other';

-- Juegos que cada chat de Telegram sigue (/seguir). La identidad sigue siendo el
-- chat_id; un chat puede seguir juegos sin estar suscrito al resumen diario
-- (is_active del suscriptor solo gobierna el resumen).
create table telegram_watchlist (
  chat_id text not null references telegram_subscribers(chat_id) on delete cascade,
  product_id uuid not null references products(id),
  -- Nivel de precio contra el que se compara: el mejor precio con stock al seguir o
  -- en el ultimo aviso. Avisamos cuando baja >= 5% bajo este nivel. Null si el juego
  -- nunca tuvo stock desde que se sigue.
  ref_price integer,
  -- Si tenia stock en la ultima revision: permite avisar cuando vuelve.
  in_stock boolean not null,
  created_at timestamptz not null default now(),
  last_alert_at timestamptz,
  primary key (chat_id, product_id)
);

create index idx_telegram_watchlist_product_id on telegram_watchlist(product_id);

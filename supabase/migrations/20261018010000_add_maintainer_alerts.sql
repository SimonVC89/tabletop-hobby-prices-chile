-- Avisos de mantenimiento (no de ofertas): por ahora, que una tienda de
-- actualizacion manual esta por cumplir el plazo en que sus listings pasan a
-- inactivos. Llegan solo a quien este marcado como mantenedor.

-- is_maintainer es independiente de is_active: el mantenedor puede darse de baja
-- del resumen de ofertas (/stop) y seguir recibiendo los avisos de mantenimiento.
-- /dar_de_baja y el bloqueo si los frenan.
alter table telegram_subscribers add column is_maintainer boolean not null default false;

-- Que avisos ya se mandaron. El episodio se identifica con la ultima vez que se
-- scrapeo la tienda: cuando se actualiza a mano, esa fecha cambia y los avisos
-- vuelven a empezar de cero, sin tener que limpiar nada.
create table maintenance_alerts (
  store_id uuid not null references stores(id),
  last_seen_at timestamptz not null,
  hours_left integer not null,
  sent_at timestamptz not null default now(),
  primary key (store_id, last_seen_at, hours_left)
);

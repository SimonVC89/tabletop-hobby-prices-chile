-- Suscriptores del bot de Telegram. La identidad es el chat_id, sin
-- cuentas ni contrasenas (FR-T2). Tres flags separados en vez de uno
-- solo porque cada uno se revierte distinto:
--   is_active            -> /stop / /start lo prenden y apagan libremente
--   opted_out_permanently -> /dar_de_baja (FR-T10), solo se revierte desde
--                            la web cuando exista el frontend
--   is_blocked           -> baneo manual por abuso, nosotros lo revertimos
create table telegram_subscribers (
  chat_id text primary key,
  is_active boolean not null default true,
  opted_out_permanently boolean not null default false,
  is_blocked boolean not null default false,
  subscribed_at timestamptz not null default now(),
  last_command_at timestamptz
);

-- Guarda el offset de Telegram getUpdates entre corridas del polling
-- (cada ~15 min, FR-T7) para no reprocesar el mismo comando dos veces.
create table telegram_bot_state (
  key text primary key,
  value text not null
);

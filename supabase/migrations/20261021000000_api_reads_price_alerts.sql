-- El comando /estado del bot dice cuando salio el ultimo resumen de ofertas, que se
-- deduce de price_alerts (las ofertas ya avisadas). Solo lectura: la tabla la escribe
-- el resumen de Python (send_telegram_digest.py) con su propio usuario.
grant select on price_alerts to thpc_api;

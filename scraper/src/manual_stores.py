"""Tiendas que no se pueden scrapear desde el cron y se actualizan a mano.

UpDown devuelve 403 especificamente a las IPs de los runners de GitHub
(trafico de datacenter), aunque funciona corrida desde una conexion normal.
Sus listings pasan a inactivos si pasan STALE_AFTER_DAYS sin verse (ver
mark_stale_listings), asi que hay que actualizarla antes de ese plazo.
"""

MANUAL_ONLY_STORES = {"UpDown"}

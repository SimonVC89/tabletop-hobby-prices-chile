package io.github.simonvc89.thpc.store;

import com.fasterxml.jackson.annotation.JsonValue;

/** Contrato {@code StoreStatus} de frontend/src/api/types.ts. */
public enum StoreStatus {
    /** Se scrapea sola dos veces al dia (cron). */
    DAILY,
    /** Bloquea las IPs de datacenter: solo se actualiza a mano. */
    MANUAL,
    /** Bloquea el acceso automatizado: se dejo de scrapear (se conserva su historial). */
    EXCLUDED;

    @JsonValue
    public String json() {
        return name().toLowerCase();
    }
}

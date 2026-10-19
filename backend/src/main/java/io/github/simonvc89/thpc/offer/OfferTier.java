package io.github.simonvc89.thpc.offer;

import com.fasterxml.jackson.annotation.JsonValue;

/** Contrato {@code OfferTier} de frontend/src/api/types.ts. */
public enum OfferTier {
    DESTACADA,
    OFERTA;

    @JsonValue
    public String json() {
        return name().toLowerCase();
    }
}

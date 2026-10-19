package io.github.simonvc89.thpc.meta;

import java.time.Instant;

/** Contrato {@code Meta} de frontend/src/api/types.ts. */
public record MetaResponse(Instant lastUpdated, long totalGames, long activeStores) {
}

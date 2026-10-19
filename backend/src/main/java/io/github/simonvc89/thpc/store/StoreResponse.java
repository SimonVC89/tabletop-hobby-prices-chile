package io.github.simonvc89.thpc.store;

import java.util.UUID;

/** Contrato {@code Store} de frontend/src/api/types.ts. */
public record StoreResponse(UUID id, String name, String baseUrl, long activeListings, StoreStatus status) {
}

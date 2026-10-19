package io.github.simonvc89.thpc.product;

import java.util.List;

/** Contrato {@code Page<T>} de frontend/src/api/types.ts. */
public record PageResponse<T>(List<T> items, int page, int pageSize, int totalItems, int totalPages) {
}

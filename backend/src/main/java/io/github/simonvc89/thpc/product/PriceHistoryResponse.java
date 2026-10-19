package io.github.simonvc89.thpc.product;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

/** Contratos {@code PriceHistory}, {@code PriceHistorySeries} y {@code PricePoint} de frontend/src/api/types.ts. */
public record PriceHistoryResponse(UUID productId, List<Series> series) {

    /** Una serie por tienda: el grafico permite mostrar u ocultar cada una. */
    public record Series(UUID storeId, String storeName, List<Point> points) {
    }

    /** Precio de una tienda en un dia (hora de Chile). */
    public record Point(LocalDate date, int price, boolean inStock) {
    }
}

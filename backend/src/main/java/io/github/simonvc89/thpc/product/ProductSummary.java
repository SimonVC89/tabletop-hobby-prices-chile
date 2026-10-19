package io.github.simonvc89.thpc.product;

import java.time.Instant;
import java.util.UUID;

/**
 * Contrato {@code ProductSummary} de frontend/src/api/types.ts: tarjeta de producto
 * en catalogo, busqueda y "relacionados".
 *
 * @param discountPct descuento del mejor precio vs. la mediana; null con menos de 3 tiendas
 * @param lastPrice   solo si esta agotado en todas las tiendas: ultimo precio visto
 * @param lastSeenAt  solo si esta agotado: cuando se vio ese ultimo precio
 */
public record ProductSummary(
        UUID id,
        String name,
        String imageUrl,
        int storeCount,
        Integer bestPrice,
        String bestStoreName,
        Integer medianPrice,
        Double discountPct,
        Integer lastPrice,
        Instant lastSeenAt) {

    public boolean inStock() {
        return bestPrice != null;
    }
}

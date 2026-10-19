package io.github.simonvc89.thpc.pricedrop;

import java.time.Instant;
import java.util.UUID;

/** Contrato {@code PriceDrop} de frontend/src/api/types.ts. */
public record PriceDropResponse(
        UUID productId,
        String productName,
        String imageUrl,
        String storeName,
        String listingUrl,
        int previousPrice,
        int price,
        double dropPct,
        Instant changedAt) {
}

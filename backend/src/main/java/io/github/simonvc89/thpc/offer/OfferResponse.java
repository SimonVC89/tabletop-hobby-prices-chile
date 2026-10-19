package io.github.simonvc89.thpc.offer;

import java.util.UUID;

/** Contrato {@code Offer} de frontend/src/api/types.ts: una tienda vendiendo bajo la mediana. */
public record OfferResponse(
        UUID productId,
        String productName,
        String imageUrl,
        String storeName,
        String listingUrl,
        int price,
        int medianPrice,
        int minPrice,
        int maxPrice,
        double discountPct,
        long storeCount,
        OfferTier tier) {
}

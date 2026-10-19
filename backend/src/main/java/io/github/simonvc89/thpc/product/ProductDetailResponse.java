package io.github.simonvc89.thpc.product;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

/** Contratos {@code ProductDetail}, {@code ProductListing} y {@code PriceStats} de frontend/src/api/types.ts. */
public record ProductDetailResponse(
        UUID id,
        String name,
        String imageUrl,
        String description,
        String descriptionSource,
        List<Listing> listings,
        Stats stats) {

    /** Uno por tienda: el listing activo mas barato con stock, o el ultimo visto si ya no lo publica. */
    public record Listing(UUID storeId, String storeName, String url, int price, boolean inStock, Instant lastSeenAt) {
    }

    public record Stats(int medianPrice, int minPrice, int maxPrice, int storeCount) {
    }
}

package io.github.simonvc89.thpc.product;

import java.util.Arrays;
import java.util.Optional;

/** Contrato {@code ProductSort} de frontend/src/api/types.ts. */
public enum ProductSort {
    RELEVANCE("relevance"),
    DISCOUNT("discount"),
    PRICE_ASC("price-asc"),
    PRICE_DESC("price-desc"),
    STORES("stores");

    private final String param;

    ProductSort(String param) {
        this.param = param;
    }

    public static Optional<ProductSort> fromParam(String value) {
        return Arrays.stream(values()).filter(s -> s.param.equals(value)).findFirst();
    }
}

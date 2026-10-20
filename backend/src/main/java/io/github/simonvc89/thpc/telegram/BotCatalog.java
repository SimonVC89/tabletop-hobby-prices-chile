package io.github.simonvc89.thpc.telegram;

import io.github.simonvc89.thpc.product.ProductCatalog;
import io.github.simonvc89.thpc.product.ProductSummary;
import java.util.List;
import org.springframework.stereotype.Component;

/**
 * Los juegos del catalogo de la API (ProductCatalog, en memoria) preparados para la
 * busqueda del bot. Se rearman solo cuando el catalogo se recarga.
 */
@Component
class BotCatalog {

    private record Index(List<ProductSummary> source, List<BotSearch.Item> items) {
    }

    private final ProductCatalog catalog;
    private volatile Index index;

    BotCatalog(ProductCatalog catalog) {
        this.catalog = catalog;
    }

    List<BotSearch.Item> items() {
        List<ProductSummary> products = catalog.all();
        Index current = index;
        if (current == null || current.source() != products) {
            current = new Index(products, products.stream()
                    .map(p -> BotSearch.Item.of(p.id(), p.name(), p.storeCount(), p.bestPrice()))
                    .toList());
            index = current;
        }
        return current.items();
    }
}

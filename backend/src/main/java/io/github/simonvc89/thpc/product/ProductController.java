package io.github.simonvc89.thpc.product;

import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    static final int MAX_PAGE_SIZE = 100;

    private final ProductCatalog catalog;
    private final ProductQueries queries;

    public ProductController(ProductCatalog catalog, ProductQueries queries) {
        this.catalog = catalog;
        this.queries = queries;
    }

    /** Busqueda del catalogo; parametros de {@code ProductQuery} (frontend/src/api/types.ts). */
    @GetMapping
    public PageResponse<ProductSummary> search(
            @RequestParam(required = false) String q,
            @RequestParam(required = false) Double minDiscount,
            @RequestParam(required = false) Integer minStores,
            @RequestParam(defaultValue = "true") boolean includeOutOfStock,
            @RequestParam(defaultValue = "relevance") String sort,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "24") int pageSize) {
        ProductSort order = ProductSort.fromParam(sort)
                .orElseThrow(() -> badRequest("sort desconocido: " + sort));
        if (page < 1 || pageSize < 1 || pageSize > MAX_PAGE_SIZE) {
            throw badRequest("page debe ser >= 1 y pageSize entre 1 y " + MAX_PAGE_SIZE);
        }
        return ProductSearch.search(catalog.all(),
                new ProductSearch.Query(q, minDiscount, minStores, includeOutOfStock, order, page, pageSize));
    }

    @GetMapping("/{id}")
    public ProductDetailResponse detail(@PathVariable String id) {
        UUID productId = visibleProduct(id).id();
        return queries.detail(productId).orElseThrow(ProductController::notFound);
    }

    @GetMapping("/{id}/price-history")
    public PriceHistoryResponse priceHistory(@PathVariable String id) {
        return queries.history(visibleProduct(id).id());
    }

    /** Hasta 6 juegos relacionados con stock; ver {@link SimilarProducts} para la regla. */
    @GetMapping("/{id}/similar")
    public List<ProductSummary> similar(@PathVariable String id) {
        ProductSummary product = visibleProduct(id);
        return SimilarProducts.select(product, queries.similarityScores(product.id()), catalog.byId());
    }

    /** Solo juegos visibles: los ocultos o fusionados responden 404, igual que un id inexistente. */
    private ProductSummary visibleProduct(String id) {
        try {
            return catalog.find(UUID.fromString(id)).orElseThrow(ProductController::notFound);
        } catch (IllegalArgumentException e) {
            throw notFound();
        }
    }

    private static ResponseStatusException notFound() {
        return new ResponseStatusException(HttpStatus.NOT_FOUND, "Juego no encontrado");
    }

    private static ResponseStatusException badRequest(String reason) {
        return new ResponseStatusException(HttpStatus.BAD_REQUEST, reason);
    }
}

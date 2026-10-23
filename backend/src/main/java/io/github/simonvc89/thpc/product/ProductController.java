package io.github.simonvc89.thpc.product;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
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
@Tag(name = "Juegos", description = "Búsqueda del catálogo y ficha de cada juego")
public class ProductController {

    static final int MAX_PAGE_SIZE = 100;
    private static final String GAME_ID = "Id del juego (UUID), por ejemplo c827edbb-d4df-4055-9e04-a95ed0070531 (Catan)";

    private final ProductCatalog catalog;
    private final ProductQueries queries;

    public ProductController(ProductCatalog catalog, ProductQueries queries) {
        this.catalog = catalog;
        this.queries = queries;
    }

    @GetMapping
    @Operation(summary = "Buscar juegos",
            description = "Busca en todos los juegos de mesa del catálogo, estén o no en oferta. Los juegos con "
                    + "stock van siempre antes que los agotados; dentro de cada grupo se aplica el orden pedido. "
                    + "De los agotados se informa el último precio visto (lastPrice) y cuándo (lastSeenAt).")
    @ApiResponse(responseCode = "200", description = "Una página de resultados")
    @ApiResponse(responseCode = "400", description = "sort desconocido, o page / pageSize fuera de rango")
    public PageResponse<ProductSummary> search(
            @Parameter(description = "Texto a buscar en el nombre; ignora tildes y mayúsculas, y deben aparecer "
                    + "todas las palabras", example = "catan")
            @RequestParam(required = false) String q,
            // Sin "example": Swagger UI rellena los campos con el ejemplo, y un filtro relleno
            // sin querer haria parecer que la busqueda no encuentra nada. Se sugiere en el texto.
            @Parameter(description = "Descuento mínimo (%) del mejor precio respecto de la mediana; por ejemplo 20 "
                    + "para ver solo ofertas")
            @RequestParam(required = false) Double minDiscount,
            @Parameter(description = "Mínimo de tiendas con stock; con 3 o más la mediana es confiable")
            @RequestParam(required = false) Integer minStores,
            @Parameter(description = "Incluir juegos agotados en todas las tiendas")
            @RequestParam(defaultValue = "true") boolean includeOutOfStock,
            @Parameter(description = "Orden de los resultados",
                    schema = @Schema(allowableValues = {"relevance", "discount", "price-asc", "price-desc", "stores"}))
            @RequestParam(defaultValue = "relevance") String sort,
            @Parameter(description = "Página, desde 1") @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "Resultados por página, de 1 a " + MAX_PAGE_SIZE)
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
    @Operation(summary = "Ficha de un juego",
            description = "Nombre, imagen, descripción corta (y de qué tienda salió), un precio por tienda (el más "
                    + "barato con stock si la tienda lo publica dos veces) de menor a mayor, y la mediana del mercado.")
    @ApiResponse(responseCode = "200", description = "La ficha")
    @ApiResponse(responseCode = "404", description = "El juego no existe, se ocultó o se fusionó con otro")
    public ProductDetailResponse detail(@Parameter(description = GAME_ID) @PathVariable String id) {
        UUID productId = visibleProduct(id).id();
        return queries.detail(productId).orElseThrow(ProductController::notFound);
    }

    @GetMapping("/{id}/price-history")
    @Operation(summary = "Historial de precios",
            description = "Un punto por tienda y día (hora de Chile) con el precio y si tenía stock. Desde el "
                    + "19-10-2026 un día sin cambios repite el precio anterior; antes de esa fecha, un día sin "
                    + "revisión queda como hueco.")
    @ApiResponse(responseCode = "200", description = "Una serie por tienda")
    @ApiResponse(responseCode = "404", description = "El juego no existe, se ocultó o se fusionó con otro")
    public PriceHistoryResponse priceHistory(@Parameter(description = GAME_ID) @PathVariable String id) {
        return queries.history(visibleProduct(id).id());
    }

    @GetMapping("/{id}/similar")
    @Operation(summary = "Juegos relacionados",
            description = "Hasta 6 juegos con stock de la misma saga (mismo inicio del nombre, con una similitud "
                    + "mínima de título) o con un título casi idéntico, según embeddings de pgvector. La saga va primero.")
    @ApiResponse(responseCode = "200", description = "Los relacionados (puede venir vacío)")
    @ApiResponse(responseCode = "404", description = "El juego no existe, se ocultó o se fusionó con otro")
    public List<ProductSummary> similar(@Parameter(description = GAME_ID) @PathVariable String id) {
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

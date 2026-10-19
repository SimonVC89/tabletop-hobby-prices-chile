package io.github.simonvc89.thpc.product;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

/** Mismas reglas que la busqueda del mock en frontend/src/api/client.ts. */
class ProductSearchTest {

    private static ProductSummary game(String name, Integer bestPrice, int storeCount, Double discount) {
        return new ProductSummary(UUID.randomUUID(), name, null, storeCount, bestPrice, null, null, discount, null, null);
    }

    private static final ProductSummary CATAN = game("Catan", 30000, 8, 10.0);
    private static final ProductSummary CATAN_CIUDADES = game("Catan: Ciudades y Caballeros", 35000, 5, 25.0);
    private static final ProductSummary CATAN_AGOTADO = game("Catan Junior", null, 0, null);
    private static final ProductSummary AZUL = game("Azul", 25000, 6, null);
    private static final ProductSummary CAFE = game("Café International", 20000, 2, null);
    private static final List<ProductSummary> ALL = List.of(CATAN_AGOTADO, AZUL, CATAN_CIUDADES, CATAN, CAFE);

    private static List<ProductSummary> search(String q, ProductSort sort) {
        return ProductSearch.search(ALL, new ProductSearch.Query(q, null, null, true, sort, 1, 24)).items();
    }

    @Test
    void ignoraTildesYMayusculas() {
        assertThat(search("CAFE", ProductSort.RELEVANCE)).containsExactly(CAFE);
    }

    @Test
    void soloQuitaAcentosNoOtrasMarcas() {
        // El selector de emoji U+FE0F se conserva, como en el mock del frontend.
        assertThat(ProductSearch.normalize("Árbol 🧙‍♂️")).isEqualTo("arbol 🧙‍♂️");
    }

    @Test
    void todasLasPalabrasDebenAparecer() {
        assertThat(search("catan ciudades", ProductSort.RELEVANCE)).containsExactly(CATAN_CIUDADES);
    }

    @Test
    void porRelevanciaElNombreExactoVaPrimeroYLosAgotadosAlFinal() {
        assertThat(search("catan", ProductSort.RELEVANCE)).containsExactly(CATAN, CATAN_CIUDADES, CATAN_AGOTADO);
    }

    @Test
    void sinTextoLaRelevanciaEsLaCantidadDeTiendas() {
        assertThat(search("", ProductSort.RELEVANCE)).containsExactly(CATAN, AZUL, CATAN_CIUDADES, CAFE, CATAN_AGOTADO);
    }

    @Test
    void porDescuentoLosSinDescuentoVanDespues() {
        assertThat(search("", ProductSort.DISCOUNT).subList(0, 2)).containsExactly(CATAN_CIUDADES, CATAN);
    }

    @Test
    void filtrosDeDescuentoTiendasYStock() {
        var conDescuento = ProductSearch.search(ALL, new ProductSearch.Query("", 20.0, null, true, ProductSort.RELEVANCE, 1, 24));
        assertThat(conDescuento.items()).containsExactly(CATAN_CIUDADES);

        var comparables = ProductSearch.search(ALL, new ProductSearch.Query("", null, 3, true, ProductSort.RELEVANCE, 1, 24));
        assertThat(comparables.items()).doesNotContain(CAFE, CATAN_AGOTADO);

        var conStock = ProductSearch.search(ALL, new ProductSearch.Query("catan", null, null, false, ProductSort.RELEVANCE, 1, 24));
        assertThat(conStock.items()).doesNotContain(CATAN_AGOTADO);
    }

    @Test
    void paginaYCuentaElTotal() {
        var page2 = ProductSearch.search(ALL, new ProductSearch.Query("", null, null, true, ProductSort.PRICE_ASC, 2, 2));
        assertThat(page2.items()).containsExactly(CATAN, CATAN_CIUDADES);
        assertThat(page2.totalItems()).isEqualTo(5);
        assertThat(page2.totalPages()).isEqualTo(3);
    }

    @Test
    void unaPaginaFueraDeRangoVieneVacia() {
        var page = ProductSearch.search(ALL, new ProductSearch.Query("", null, null, true, ProductSort.RELEVANCE, 9, 24));
        assertThat(page.items()).isEmpty();
        assertThat(page.totalPages()).isEqualTo(1);
    }
}

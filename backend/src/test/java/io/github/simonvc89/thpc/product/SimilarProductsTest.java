package io.github.simonvc89.thpc.product;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

class SimilarProductsTest {

    // Los mismos casos que tenia scraper/tests/test_matching.py (test_clave_de_saga).
    @ParameterizedTest
    @CsvSource({
            "Catan Junior, catan",
            "'Catán: Navegantes', catan",
            "El Señor de los Anillos LCG, senor",
            "7 Wonders Duel, 7 wonders",
            "Ark Nova, ark nova",
            "'Star Realms: Escenarios', star realms",  // prefijo ambiguo: dos palabras
            "Star Wars Rivals, star wars",
    })
    void laSagaEsElInicioDelNombre(String name, String expected) {
        assertThat(SimilarProducts.familyKey(name)).isEqualTo(expected);
    }

    @ParameterizedTest
    @ValueSource(strings = {"Juego de dados clásico", "Pack de cartas", "Juego de Tronos"})
    void sinSagaSiElNombreEmpiezaConUnaPalabraGenerica(String name) {
        assertThat(SimilarProducts.familyKey(name)).isNull();
    }

    private static ProductSummary game(String name, boolean inStock) {
        return new ProductSummary(UUID.randomUUID(), name, null, 3, inStock ? 10000 : null, null, null, null, null, null);
    }

    @Test
    void entranLaMismaSagaConSimilitudMinimaYLosCasiIdenticos() {
        var catan = game("Catan", true);
        var junior = game("Catan Junior", true);           // saga, 0.50 >= 0.45
        var parecido = game("Catalina Express", true);     // otra saga, 0.80 >= 0.78
        var lejano = game("Carcassonne", true);            // otra saga, 0.60 < 0.78
        var agotado = game("Catan Ciudades", false);       // sin stock
        var catalog = Map.of(catan.id(), catan, junior.id(), junior, parecido.id(), parecido,
                lejano.id(), lejano, agotado.id(), agotado);
        var scores = Map.of(catan.id(), 1.0, junior.id(), 0.50, parecido.id(), 0.80,
                lejano.id(), 0.60, agotado.id(), 0.95);

        // La saga suma 0.15 (Catan Junior queda en 0.65), pero el casi identico (0.80) sigue primero.
        assertThat(SimilarProducts.select(catan, scores, catalog)).containsExactly(parecido, junior);
    }
}

package io.github.simonvc89.thpc.pricedrop;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import java.util.stream.IntStream;
import org.junit.jupiter.api.Test;

/** Mismos casos que scraper/tests/test_price_drops.py. */
class PriceDropSelectorTest {

    private static final Instant WHEN = Instant.parse("2026-10-19T15:44:00Z");

    private static PriceDropSelector.Candidate row(String product, int previous, int price, String store) {
        UUID id = UUID.nameUUIDFromBytes(product.getBytes(StandardCharsets.UTF_8));
        return new PriceDropSelector.Candidate(id, product, null, store, "https://x.cl/" + product, previous, price, WHEN);
    }

    private static PriceDropSelector.Candidate row(String product, int previous, int price) {
        return row(product, previous, price, "Tienda");
    }

    @Test
    void descartaBajasMenoresAlUmbral() {
        var drops = PriceDropSelector.select(List.of(row("A", 10000, 9600), row("B", 10000, 9500)), 5, 12);
        assertThat(drops).extracting(PriceDropResponse::productName).containsExactly("B");
    }

    @Test
    void unJuegoApareceUnaVezConSuMayorBaja() {
        var drops = PriceDropSelector.select(List.of(row("A", 10000, 9000, "T1"), row("A", 10000, 7000, "T2")));
        assertThat(drops).hasSize(1);
        assertThat(drops.getFirst().storeName()).isEqualTo("T2");
        assertThat(drops.getFirst().dropPct()).isEqualTo(30.0);
    }

    @Test
    void ordenDeMayorAMenorYTope() {
        var data = IntStream.range(0, 20).mapToObj(i -> row(String.valueOf(i), 10000, 10000 - 100 * (i + 5))).toList();
        var drops = PriceDropSelector.select(data, 5, 12);
        assertThat(drops).hasSize(12);
        assertThat(drops.getFirst().dropPct()).isGreaterThanOrEqualTo(drops.getLast().dropPct());
    }

    @Test
    void calculaElPorcentajeConUnDecimal() {
        var drop = PriceDropSelector.select(List.of(row("Catan", 29990, 24990))).getFirst();
        assertThat(drop.dropPct()).isEqualTo(16.7);
        assertThat(drop.previousPrice()).isEqualTo(29990);
        assertThat(drop.changedAt()).isEqualTo(WHEN);
    }
}

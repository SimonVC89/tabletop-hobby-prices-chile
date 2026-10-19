package io.github.simonvc89.thpc.product;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.tuple;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class PriceHistoryBuilderTest {

    private static final UUID STORE_A = UUID.randomUUID();
    private static final UUID STORE_B = UUID.randomUUID();
    private static final UUID LISTING_1 = UUID.randomUUID();
    private static final UUID LISTING_2 = UUID.randomUUID();
    private static final LocalDate CHANGES_FROM = LocalDate.of(2026, 10, 19);

    private static LocalDate oct(int day) {
        return LocalDate.of(2026, 10, day);
    }

    private static PriceHistoryBuilder.Row row(UUID listing, UUID store, String storeName, LocalDate day, int price,
                                               boolean inStock) {
        return new PriceHistoryBuilder.Row(listing, store, storeName, true, day, day, price, inStock);
    }

    private static List<PriceHistoryResponse.Point> points(List<PriceHistoryResponse.Series> series, int index) {
        return series.get(index).points();
    }

    @Test
    void desdeElRegistroDeCambiosUnDiaSinFilaRepiteElPrecioAnterior() {
        var series = PriceHistoryBuilder.build(List.of(
                row(LISTING_1, STORE_A, "A", oct(19), 10000, true),
                row(LISTING_1, STORE_A, "A", oct(22), 9000, true)), oct(23), CHANGES_FROM);

        assertThat(points(series, 0)).extracting(PriceHistoryResponse.Point::date, PriceHistoryResponse.Point::price)
                .containsExactly(
                        tuple(oct(19), 10000),
                        tuple(oct(20), 10000),
                        tuple(oct(21), 10000),
                        tuple(oct(22), 9000),
                        tuple(oct(23), 9000));
    }

    @Test
    void antesDelRegistroDeCambiosUnDiaSinScrapingQuedaComoHueco() {
        // La tienda tuvo scraping el 15 y el 17, no el 16: el 16 no se rellena.
        var series = PriceHistoryBuilder.build(List.of(
                row(LISTING_1, STORE_A, "A", oct(15), 10000, true),
                row(LISTING_1, STORE_A, "A", oct(17), 10000, true)), oct(17), CHANGES_FROM);

        assertThat(points(series, 0)).extracting(PriceHistoryResponse.Point::date).containsExactly(oct(15), oct(17));
    }

    @Test
    void enUnaTiendaConDosPaginasGanaLaConStockYLuegoLaMasBarata() {
        var series = PriceHistoryBuilder.build(List.of(
                row(LISTING_1, STORE_A, "A", oct(19), 8000, false),
                row(LISTING_2, STORE_A, "A", oct(19), 12000, true)), oct(19), CHANGES_FROM);

        assertThat(points(series, 0)).singleElement()
                .satisfies(p -> {
                    assertThat(p.price()).isEqualTo(12000);
                    assertThat(p.inStock()).isTrue();
                });
    }

    @Test
    void unListingQueYaNoSePublicaTerminaElUltimoDiaQueSeVio() {
        var gone = new PriceHistoryBuilder.Row(LISTING_1, STORE_A, "A", false, oct(20), oct(19), 10000, true);
        var series = PriceHistoryBuilder.build(List.of(gone), oct(25), CHANGES_FROM);

        assertThat(points(series, 0)).extracting(PriceHistoryResponse.Point::date).containsExactly(oct(19), oct(20));
    }

    @Test
    void lasSeriesVanOrdenadasPorNombreDeTienda() {
        var series = PriceHistoryBuilder.build(List.of(
                row(LISTING_1, STORE_B, "Zeta", oct(19), 10000, true),
                row(LISTING_2, STORE_A, "Alfa", oct(19), 10000, true)), oct(19), CHANGES_FROM);

        assertThat(series).extracting(PriceHistoryResponse.Series::storeName).containsExactly("Alfa", "Zeta");
    }
}

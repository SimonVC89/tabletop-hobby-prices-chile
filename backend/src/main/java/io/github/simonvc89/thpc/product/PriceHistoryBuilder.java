package io.github.simonvc89.thpc.product;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.UUID;

/**
 * Arma el historial diario de un juego a partir de price_history, que guarda solo
 * cambios. Misma logica que export_details en scraper/src/export_frontend_snapshot.py.
 *
 * <p>El estado de un listing vale desde su fila hasta el dia anterior a la siguiente,
 * y la ultima fila hasta la ultima vez que la tienda mostro el listing (o hasta el
 * ultimo scraping si sigue activo). Un punto por tienda y dia: con stock primero, y
 * el mas barato (algunas tiendas publican el mismo juego en dos paginas).
 */
public final class PriceHistoryBuilder {

    /**
     * Primer dia (hora de Chile) en que price_history guarda solo cambios. Antes se
     * guardaba una fila por scraping, asi que un dia sin fila es un dia SIN scraping
     * (desconocido): no se rellena y el grafico muestra el hueco.
     */
    public static final LocalDate CHANGES_ONLY_FROM = LocalDate.of(2026, 10, 19);

    /**
     * Una fila de price_history con los datos de su listing. Dias en hora de Chile.
     *
     * @param listingActive si la tienda sigue mostrando el listing
     * @param seenDay       ultimo dia en que la tienda mostro el listing
     */
    public record Row(UUID listingId, UUID storeId, String storeName, boolean listingActive, LocalDate seenDay,
                      LocalDate day, int price, boolean inStock) {
    }

    private record State(int price, boolean inStock) {
        /** Con stock antes que sin stock; a igualdad, el mas barato. */
        boolean betterThan(State other) {
            if (inStock != other.inStock) {
                return inStock;
            }
            return price < other.price;
        }
    }

    private PriceHistoryBuilder() {
    }

    /**
     * @param rows          filas ordenadas por listing y momento del scraping
     * @param lastScrapeDay dia del ultimo scraping (hasta donde se extienden los listings activos)
     */
    public static List<PriceHistoryResponse.Series> build(List<Row> rows, LocalDate lastScrapeDay,
                                                          LocalDate changesOnlyFrom) {
        // listing -> dia -> estado; si hay dos filas el mismo dia, manda la ultima.
        Map<UUID, TreeMap<LocalDate, State>> listingDays = new LinkedHashMap<>();
        Map<UUID, Row> listingInfo = new HashMap<>();
        for (Row r : rows) {
            listingDays.computeIfAbsent(r.listingId(), id -> new TreeMap<>()).put(r.day(), new State(r.price(), r.inStock()));
            listingInfo.put(r.listingId(), r);
        }

        // Dias con scraping de cada tienda, anteriores al registro de solo cambios.
        Map<UUID, Set<LocalDate>> scrapedDays = new HashMap<>();
        listingDays.forEach((listingId, days) -> scrapedDays
                .computeIfAbsent(listingInfo.get(listingId).storeId(), id -> new HashSet<>())
                .addAll(days.headMap(changesOnlyFrom).keySet()));

        Map<UUID, TreeMap<LocalDate, State>> byStore = new LinkedHashMap<>();
        Map<UUID, String> storeNames = new HashMap<>();
        listingDays.forEach((listingId, days) -> {
            Row info = listingInfo.get(listingId);
            storeNames.put(info.storeId(), info.storeName());
            LocalDate end = info.listingActive() ? lastScrapeDay : info.seenDay();
            Set<LocalDate> known = scrapedDays.get(info.storeId());
            TreeMap<LocalDate, State> storeDays = byStore.computeIfAbsent(info.storeId(), id -> new TreeMap<>());

            List<Map.Entry<LocalDate, State>> ordered = new ArrayList<>(days.entrySet());
            for (int i = 0; i < ordered.size(); i++) {
                LocalDate day = ordered.get(i).getKey();
                State state = ordered.get(i).getValue();
                LocalDate stop = i + 1 < ordered.size() ? ordered.get(i + 1).getKey().minusDays(1) : end;
                long span = Math.max(ChronoUnit.DAYS.between(day, stop), 0);
                for (long offset = 0; offset <= span; offset++) {
                    LocalDate d = day.plusDays(offset);
                    if (offset > 0 && d.isBefore(changesOnlyFrom) && !known.contains(d)) {
                        continue;
                    }
                    State current = storeDays.get(d);
                    if (current == null || state.betterThan(current)) {
                        storeDays.put(d, state);
                    }
                }
            }
        });

        List<PriceHistoryResponse.Series> series = new ArrayList<>();
        byStore.forEach((storeId, days) -> series.add(new PriceHistoryResponse.Series(storeId, storeNames.get(storeId),
                days.entrySet().stream()
                        .map(e -> new PriceHistoryResponse.Point(e.getKey(), e.getValue().price(), e.getValue().inStock()))
                        .toList())));
        series.sort(Comparator.comparing(PriceHistoryResponse.Series::storeName));
        return series;
    }
}

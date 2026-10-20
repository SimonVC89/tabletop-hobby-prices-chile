package io.github.simonvc89.thpc.pricedrop;

import java.time.Instant;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Elige que bajas mostrar en "Bajaron en las ultimas 24 horas" (pagina de Inicio).
 */
public final class PriceDropSelector {

    /** Ventana de la seccion. */
    public static final int WINDOW_HOURS = 24;
    /** El mismo umbral que los avisos de juegos seguidos por Telegram. */
    public static final double MIN_PCT = 5;
    public static final int LIMIT = 12;

    /** Un cambio de precio candidato: ultima fila de un listing, mas barata que la anterior. */
    public record Candidate(
            UUID productId,
            String productName,
            String imageUrl,
            String storeName,
            String listingUrl,
            int previousPrice,
            int price,
            Instant changedAt) {
    }

    private PriceDropSelector() {
    }

    /** Una baja por juego (la mayor), de al menos {@code minPct}%, de mayor a menor, hasta {@code limit}. */
    public static List<PriceDropResponse> select(List<Candidate> candidates, double minPct, int limit) {
        Map<UUID, PriceDropResponse> best = new LinkedHashMap<>();
        for (Candidate c : candidates) {
            double pct = Math.round(1000.0 * (c.previousPrice() - c.price()) / c.previousPrice()) / 10.0;
            if (pct < minPct) {
                continue;
            }
            PriceDropResponse current = best.get(c.productId());
            if (current == null || pct > current.dropPct()) {
                best.put(c.productId(), new PriceDropResponse(c.productId(), c.productName(), c.imageUrl(),
                        c.storeName(), c.listingUrl(), c.previousPrice(), c.price(), pct, c.changedAt()));
            }
        }
        return best.values().stream()
                .sorted(Comparator.comparingDouble(PriceDropResponse::dropPct).reversed()
                        .thenComparing(PriceDropResponse::productName))
                .limit(limit)
                .toList();
    }

    public static List<PriceDropResponse> select(List<Candidate> candidates) {
        return select(candidates, MIN_PCT, LIMIT);
    }
}

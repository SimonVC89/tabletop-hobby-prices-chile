package io.github.simonvc89.thpc.product;

import java.text.Collator;
import java.text.Normalizer;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import java.util.regex.Pattern;

/**
 * Busqueda del catalogo: filtra, ordena y pagina. Replica lo que hacia el mock del
 * frontend (frontend/src/api/client.ts) para que cambiar del snapshot a la API no
 * cambie los resultados. Los juegos con stock van siempre antes que los agotados.
 */
public final class ProductSearch {

    /** Parametros de {@code ProductQuery} (frontend/src/api/types.ts). */
    public record Query(
            String q,
            Double minDiscount,
            Integer minStores,
            boolean includeOutOfStock,
            ProductSort sort,
            int page,
            int pageSize) {
    }

    private static final Pattern MARKS = Pattern.compile("\\p{M}+");
    private static final Pattern SPACES = Pattern.compile("\\s+");
    private static final Pattern NON_WORD = Pattern.compile("[^a-z0-9]+");
    private static final Collator NAME_ORDER = Collator.getInstance(Locale.of("es"));

    private ProductSearch() {
    }

    /** Sin tildes y en minusculas: "Café" y "cafe" son lo mismo. */
    static String normalize(String s) {
        return MARKS.matcher(Normalizer.normalize(s, Normalizer.Form.NFD)).replaceAll("").toLowerCase(Locale.ROOT);
    }

    public static PageResponse<ProductSummary> search(List<ProductSummary> all, Query query) {
        String q = query.q() == null ? "" : normalize(query.q()).trim();
        List<String> terms = q.isEmpty() ? List.of() : Arrays.asList(SPACES.split(q));

        List<ProductSummary> items = all.stream()
                .filter(p -> terms.stream().allMatch(normalize(p.name())::contains))
                .filter(p -> query.minDiscount() == null || discount(p) >= query.minDiscount())
                .filter(p -> query.minStores() == null || p.storeCount() >= query.minStores())
                .filter(p -> query.includeOutOfStock() || p.inStock())
                .sorted(order(query.sort(), q, terms))
                .toList();

        int total = items.size();
        int from = Math.min((query.page() - 1) * query.pageSize(), total);
        int to = Math.min(from + query.pageSize(), total);
        int totalPages = Math.max(1, (int) Math.ceil((double) total / query.pageSize()));
        return new PageResponse<>(items.subList(from, to), query.page(), query.pageSize(), total, totalPages);
    }

    private static double discount(ProductSummary p) {
        return p.discountPct() == null ? 0 : p.discountPct();
    }

    private static Comparator<ProductSummary> order(ProductSort sort, String q, List<String> terms) {
        Comparator<ProductSummary> byPrice = Comparator.comparingDouble(
                p -> p.bestPrice() == null ? Double.POSITIVE_INFINITY : p.bestPrice());

        Comparator<ProductSummary> criterion = switch (sort) {
            case DISCOUNT -> Comparator.comparingDouble(
                    (ProductSummary p) -> p.discountPct() == null ? -1 : p.discountPct()).reversed();
            case PRICE_ASC -> byPrice;
            case PRICE_DESC -> byPrice.reversed();
            case STORES -> Comparator.comparingInt(ProductSummary::storeCount).reversed();
            case RELEVANCE -> {
                // Sin texto, "relevancia" = los mas comparables primero.
                Map<UUID, Double> scores = new HashMap<>();
                Comparator<ProductSummary> byScore = Comparator.comparingDouble(
                        (ProductSummary p) -> q.isEmpty() ? 0 : scores.computeIfAbsent(p.id(), id -> relevance(p.name(), q, terms)))
                        .reversed();
                yield byScore.thenComparing(Comparator.comparingInt(ProductSummary::storeCount).reversed());
            }
        };

        return Comparator.comparing((ProductSummary p) -> !p.inStock())
                .thenComparing(criterion)
                .thenComparing(ProductSummary::name, NAME_ORDER);
    }

    /**
     * Que tan bien calza un nombre con la busqueda: nombre exacto, luego que empiece
     * igual, luego palabras que empiecen con cada termino. A igualdad, nombres mas
     * cortos primero (el juego base antes que sus expansiones).
     */
    static double relevance(String name, String query, List<String> terms) {
        String n = normalize(name);
        String[] words = NON_WORD.split(n);
        double score = 0;
        if (n.equals(query)) {
            score += 100;
        } else if (n.startsWith(query)) {
            score += 50;
        }
        for (String t : terms) {
            if (Arrays.stream(words).anyMatch(w -> w.startsWith(t))) {
                score += 10;
            }
        }
        return score - n.length() / 100.0;
    }
}

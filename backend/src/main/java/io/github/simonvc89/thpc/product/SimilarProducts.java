package io.github.simonvc89.thpc.product;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.regex.Pattern;

/**
 * Juegos relacionados: de la misma saga o con titulo casi identico, solo con stock.
 *
 * <p>Los embeddings son de TITULOS: captan sagas y nombres parecidos, no mecanicas
 * (a Azul le salian "Bluey"). Por eso solo entran juegos de la misma saga con un
 * minimo de similitud, o juegos con titulo casi identico.
 */
public final class SimilarProducts {

    public static final int COUNT = 6;
    /** Las ediciones con licencia ("Dobble Paw Patrol") comparten saga con similitud ~0.5. */
    static final double FAMILY_MIN_SCORE = 0.45;
    static final double SIMILAR_MIN_SCORE = 0.78;
    /** La saga va antes que un parecido por embedding. */
    static final double FAMILY_BONUS = 0.15;

    private static final Set<String> FAMILY_STOPWORDS = Set.of("el", "la", "los", "las", "un", "una", "the", "de", "del");
    /** Primeras palabras que no identifican una saga ("Juego de ...", "Pack ..."). */
    private static final Set<String> GENERIC_FIRST_WORDS = Set.of(
            "juego", "juegos", "pack", "kit", "set", "caja", "mini", "super", "gran", "expansion",
            "ampliacion", "cartas", "tablero", "mazo", "tapete", "dados", "libro", "guia");
    /** Compartidas por sagas sin relacion ("Star Realms" / "Star Wars"): ahi se usan dos palabras. */
    private static final Set<String> AMBIGUOUS_FIRST_WORDS = Set.of(
            "star", "dark", "black", "blue", "red", "white", "gold", "golden", "love", "happy", "little", "big", "mega");

    private static final Pattern MARKS = Pattern.compile("\\p{M}+");
    private static final Pattern NON_WORD = Pattern.compile("[^a-z0-9]+");

    private SimilarProducts() {
    }

    /** Saga de un juego por el inicio de su nombre ("Catan Junior" -> "catan"); null si no se puede saber. */
    static String familyKey(String name) {
        String plain = MARKS.matcher(Normalizer.normalize(name, Normalizer.Form.NFKD)).replaceAll("").toLowerCase(Locale.ROOT);
        List<String> words = new ArrayList<>(Arrays.stream(NON_WORD.split(plain)).filter(w -> !w.isEmpty()).toList());
        while (!words.isEmpty() && FAMILY_STOPWORDS.contains(words.getFirst())) {
            words.removeFirst();
        }
        if (words.isEmpty() || GENERIC_FIRST_WORDS.contains(words.getFirst())) {
            return null;
        }
        String first = words.getFirst();
        if (first.length() >= 4 && !AMBIGUOUS_FIRST_WORDS.contains(first)) {
            return first;
        }
        // Palabra inicial corta ("7 Wonders", "Ark Nova"): se necesitan dos.
        return words.size() >= 2 ? first + " " + words.get(1) : null;
    }

    /**
     * @param target  el juego de la ficha
     * @param scores  similitud coseno de cada juego con el target (solo juegos con embedding)
     * @param catalog juegos visibles, para nombre y stock
     */
    public static List<ProductSummary> select(ProductSummary target, Map<UUID, Double> scores,
                                              Map<UUID, ProductSummary> catalog) {
        String family = familyKey(target.name());
        record Ranked(ProductSummary product, double rank) {
        }

        List<Ranked> eligible = new ArrayList<>();
        scores.forEach((id, score) -> {
            ProductSummary p = catalog.get(id);
            if (p == null || id.equals(target.id()) || !p.inStock()) {
                return;
            }
            boolean sameFamily = family != null && family.equals(familyKey(p.name()));
            if (score >= SIMILAR_MIN_SCORE || (sameFamily && score >= FAMILY_MIN_SCORE)) {
                eligible.add(new Ranked(p, score + (sameFamily ? FAMILY_BONUS : 0)));
            }
        });
        return eligible.stream()
                .sorted(Comparator.comparingDouble(Ranked::rank).reversed())
                .limit(COUNT)
                .map(Ranked::product)
                .toList();
    }
}

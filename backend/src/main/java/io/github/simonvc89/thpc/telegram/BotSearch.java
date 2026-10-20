package io.github.simonvc89.thpc.telegram;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Busqueda de juegos para /seguir: logica pura, sin base de datos. Misma regla que
 * scraper/src/telegram_watchlist.py (que la uso mientras el bot leia por polling):
 * <ul>
 *   <li>cada palabra escrita es un prefijo ("nav" encuentra "Navegantes"), sin
 *       importar tildes, mayusculas ni orden;</li>
 *   <li>entiende sinonimos ("exp", "ampliacion" y "expansion" son lo mismo);</li>
 *   <li>si no encuentra nada, corrige errores de tipeo ("catna" -> "catan");</li>
 *   <li>con muchos resultados sugiere palabras para acotar y permite paginar.</li>
 * </ul>
 */
public final class BotSearch {

    public static final int MAX_OPTIONS = 5;
    /** Telegram solo convierte en enlace un comando corto: si la busqueda no cabe, no se ofrece "ver mas". */
    static final int MAX_COMMAND_LENGTH = 60;
    /** Una palabra muy corta no se corrige: "ark" podria ser cualquier cosa. */
    static final int MIN_CORRECTABLE_LENGTH = 4;
    static final double TYPO_CUTOFF = 0.75;
    /** Primeros caracteres del id del producto: el codigo tocable de /seguir_xxxx. */
    static final int CODE_LENGTH = 8;

    /** Palabras que no ayudan a acotar: conectores y "juego"/"mesa", que estan en casi todo. */
    private static final Set<String> STOPWORDS = Set.of(
            "de", "del", "la", "el", "los", "las", "y", "en", "con", "para", "un", "una", "the", "of", "and", "por",
            "al", "lo", "juego", "mesa");
    /** Como mostrar las palabras que son sinonimos canonicos (la clave va sin tilde). */
    private static final Map<String, String> DISPLAY = Map.of(
            "expansion", "expansión", "edicion", "edición", "jugadores", "jugadores");

    // Mismos sinonimos y ordinales que scraper/src/matching/normalize.py (canonical).
    private static final Map<String, String> SYNONYMS = Map.of(
            "primera", "ord1", "segunda", "ord2", "tercera", "ord3", "cuarta", "ord4",
            "exp", "expansion", "ampliacion", "expansion", "jug", "jugadores", "ed", "edicion");
    /** "2da", "2a", "3ra", "3era", "2o" -> "ord2", "ord3". */
    private static final Pattern ORDINAL = Pattern.compile("(\\d+)(?:da|ra|ta|na|ma|va|era|a|o)");

    private static final Pattern MARKS = Pattern.compile("\\p{M}+");
    private static final Pattern NON_ALNUM = Pattern.compile("[^a-z0-9]+");
    private static final Pattern WORD = Pattern.compile("[\\p{L}\\p{N}]+");
    private static final Pattern CODE = Pattern.compile("[0-9a-f]{" + CODE_LENGTH + "}");

    /** Un juego del catalogo, con su nombre ya preparado para buscar. */
    public record Item(UUID id, String name, int stores, Integer price, String normalized, List<List<String>> forms) {

        public static Item of(UUID id, String name, int stores, Integer price) {
            String normalized = norm(name);
            List<List<String>> forms = normalized.isEmpty()
                    ? List.of()
                    : Arrays.stream(normalized.split(" ")).map(BotSearch::forms).toList();
            return new Item(id, name, stores, price, normalized, forms);
        }
    }

    /** Resultado de una busqueda; {@code corrected} solo si hubo que corregir errores de tipeo. */
    public record Result(List<Item> matches, List<String> terms, String corrected) {
    }

    private BotSearch() {
    }

    static String stripAccents(String text) {
        return MARKS.matcher(Normalizer.normalize(text, Normalizer.Form.NFKD)).replaceAll("");
    }

    /** Sin tildes, en minusculas y solo letras y numeros separados por un espacio. */
    static String norm(String text) {
        return NON_ALNUM.matcher(stripAccents(text).toLowerCase(Locale.ROOT)).replaceAll(" ").strip();
    }

    static List<String> terms(String query) {
        String n = norm(query);
        return n.isEmpty() ? List.of() : List.of(n.split(" "));
    }

    static String canonical(String word) {
        Matcher m = ORDINAL.matcher(word);
        return m.matches() ? "ord" + m.group(1) : SYNONYMS.getOrDefault(word, word);
    }

    /** La palabra y, si es un sinonimo, su forma canonica ("ampliacion" -> tambien "expansion"). */
    static List<String> forms(String token) {
        String canon = canonical(token);
        return canon.equals(token) ? List.of(token) : List.of(token, canon);
    }

    private static boolean termMatches(String term, List<List<String>> tokenForms) {
        List<String> wanted = forms(term);
        for (List<String> forms : tokenForms) {
            for (String form : forms) {
                for (String w : wanted) {
                    if (form.startsWith(w)) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    /**
     * Juegos que contienen todas las palabras (como prefijos). Primero el nombre exacto,
     * luego los que tienen stock, luego los nombres mas cortos (el juego base antes que
     * sus expansiones) y los mas comparables.
     */
    static List<Item> matchCatalog(List<Item> catalog, List<String> terms) {
        String exact = String.join(" ", terms);
        List<Item> matches = new ArrayList<>();
        for (Item item : catalog) {
            if (terms.stream().allMatch(t -> termMatches(t, item.forms()))) {
                matches.add(item);
            }
        }
        matches.sort(Comparator
                .comparing((Item m) -> !m.normalized().equals(exact))
                .thenComparing(m -> m.price() == null)
                .thenComparingInt(m -> m.name().codePointCount(0, m.name().length()))
                .thenComparing(Comparator.comparingInt(Item::stores).reversed()));
        return matches;
    }

    /** Reemplaza las palabras que no existen en ningun nombre por la mas parecida (si hay). */
    static List<String> correctTerms(List<Item> catalog, List<String> terms) {
        Set<String> vocabulary = new LinkedHashSet<>();
        for (Item item : catalog) {
            for (List<String> forms : item.forms()) {
                vocabulary.add(forms.getFirst());
            }
        }
        List<String> corrected = new ArrayList<>();
        for (String term : terms) {
            List<String> termForms = forms(term);
            boolean known = vocabulary.stream().anyMatch(tok -> termForms.stream().anyMatch(tok::startsWith));
            if (known || term.length() < MIN_CORRECTABLE_LENGTH) {
                corrected.add(term);
            } else {
                corrected.add(Difflib.closeMatch(term, vocabulary, TYPO_CUTOFF).orElse(term));
            }
        }
        return corrected;
    }

    /** Busca y, si no encuentra nada, reintenta con los errores de tipeo corregidos. */
    public static Result search(List<Item> catalog, String query) {
        List<String> terms = terms(query);
        if (terms.isEmpty()) {
            return new Result(List.of(), List.of(), null);
        }
        List<Item> matches = matchCatalog(catalog, terms);
        if (matches.isEmpty()) {
            List<String> fixed = correctTerms(catalog, terms);
            if (!fixed.equals(terms)) {
                List<Item> retry = matchCatalog(catalog, fixed);
                if (!retry.isEmpty()) {
                    return new Result(retry, fixed, String.join(" ", fixed));
                }
            }
        }
        return new Result(matches, terms, null);
    }

    /**
     * Palabras que mejor separan los resultados: presentes en varios pero no en todos.
     * Sirven para decir que agregar a la busqueda ("campaña", "investigadores"...).
     */
    static List<String> narrowingWords(List<Item> matches, List<String> terms, int limit) {
        int total = matches.size();
        Set<String> asked = new HashSet<>();
        terms.forEach(t -> asked.addAll(forms(t)));
        Map<String, Integer> counts = new LinkedHashMap<>();
        Map<String, String> shown = new LinkedHashMap<>();
        for (Item item : matches) {
            Set<String> seen = new HashSet<>();
            Matcher words = WORD.matcher(item.name());
            while (words.find()) {
                String original = words.group();
                String token = norm(original);
                if (token.isEmpty() || STOPWORDS.contains(token) || token.length() < 4 || isDigits(token)) {
                    continue;
                }
                String key = canonical(token);
                if (seen.contains(key) || asked.stream().anyMatch(a -> key.startsWith(a) || token.startsWith(a))) {
                    continue;
                }
                seen.add(key);
                counts.merge(key, 1, Integer::sum);
                // Se muestra la forma con tilde si algun nombre la trae ("campaña", no "campana").
                String candidate = DISPLAY.getOrDefault(key, original.toLowerCase(Locale.ROOT));
                if (!shown.containsKey(key) || accents(candidate) > accents(shown.get(key))) {
                    shown.put(key, candidate);
                }
            }
        }
        record Scored(int score, String key) {
        }
        List<Scored> scored = counts.entrySet().stream()
                .filter(e -> e.getValue() >= 2 && e.getValue() < total)
                .map(e -> new Scored(Math.min(e.getValue(), total - e.getValue()), e.getKey()))
                .sorted(Comparator.comparingInt((Scored s) -> -s.score())
                        .thenComparingInt(s -> s.key().length())
                        .thenComparing(Scored::key))
                .toList();

        List<String> chosen = new ArrayList<>();
        for (Scored s : scored) {
            // Singular y plural son la misma pista ("investigador" / "investigadores").
            if (chosen.stream().anyMatch(other -> s.key().startsWith(other) || other.startsWith(s.key()))) {
                continue;
            }
            chosen.add(s.key());
            if (chosen.size() == limit) {
                break;
            }
        }
        return chosen.stream().map(shown::get).toList();
    }

    private static boolean isDigits(String token) {
        return token.chars().allMatch(Character::isDigit);
    }

    /** Cuantas letras con tilde o ñ tiene un texto (para preferir la forma bien escrita). */
    private static long accents(String text) {
        return text.codePoints()
                .filter(cp -> !stripAccents(Character.toString(cp)).contains(Character.toString(cp)))
                .count();
    }

    /** Comando tocable para ver otra pagina; vacio si la busqueda no cabe en un comando. */
    static Optional<String> moreCommand(int page, List<String> terms) {
        String command = "/mas_" + page + "_" + String.join("_", terms);
        return command.length() <= MAX_COMMAND_LENGTH ? Optional.of(command) : Optional.empty();
    }

    /** Pagina pedida en /mas_&lt;pagina&gt;_&lt;palabras&gt;. */
    record MoreRequest(int page, List<String> terms) {
    }

    /** "2_arkham_horror_lcg" -> pagina 2, [arkham, horror, lcg]; vacio si no es valido. */
    static Optional<MoreRequest> parseMoreCommand(String rest) {
        int sep = rest.indexOf('_');
        String page = sep < 0 ? rest : rest.substring(0, sep);
        String query = sep < 0 ? "" : rest.substring(sep + 1);
        List<String> terms = Arrays.stream(query.split("_")).filter(t -> !t.isEmpty()).toList();
        // Mas de 6 cifras no es una pagina real (y evita desbordar el int).
        if (page.isEmpty() || page.length() > 6 || !isDigits(page) || Integer.parseInt(page) < 2 || terms.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(new MoreRequest(Integer.parseInt(page), terms));
    }

    /** Codigo corto y tocable del producto: la primera parte de su UUID. */
    static String codeOf(UUID productId) {
        return productId.toString().substring(0, CODE_LENGTH);
    }

    static boolean isValidCode(String code) {
        return CODE.matcher(code).matches();
    }

    /** 31990 -> "$31.990" (formato del bot, igual que en Python). */
    static String clp(int value) {
        return "$" + String.format(Locale.ROOT, "%,d", value).replace(',', '.');
    }
}

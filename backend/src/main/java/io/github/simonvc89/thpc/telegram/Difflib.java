package io.github.simonvc89.thpc.telegram;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Deque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Port de lo que el bot usaba de difflib (Python): SequenceMatcher.ratio y
 * get_close_matches con n=1. Java no trae un equivalente, y otro algoritmo de
 * similitud corregiria distinto los errores de tipeo ("catna" -> "catan"); por
 * eso se replica el de Python (Ratcliff/Obershelp) paso a paso.
 *
 * <p>Sin "junk" ni la heuristica autojunk de difflib: esa solo se activa con
 * secuencias de 200+ caracteres, y aqui se comparan palabras.
 */
final class Difflib {

    private Difflib() {
    }

    /** SequenceMatcher(None, a, b).ratio(): 2 * coincidencias / largo total, entre 0 y 1. */
    static double ratio(String a, String b) {
        int total = a.length() + b.length();
        return total == 0 ? 1.0 : 2.0 * matchingCharacters(a, b) / total;
    }

    /**
     * get_close_matches(word, possibilities, n=1, cutoff): la posibilidad mas
     * parecida con ratio >= cutoff. A igual ratio gana la mayor alfabeticamente,
     * como heapq.nlargest sobre tuplas (ratio, palabra).
     */
    static Optional<String> closeMatch(String word, Collection<String> possibilities, double cutoff) {
        String best = null;
        double bestScore = -1;
        for (String candidate : possibilities) {
            // Cotas superiores baratas de ratio (real_quick_ratio y quick_ratio) antes del calculo caro.
            if (realQuickRatio(candidate, word) < cutoff || quickRatio(candidate, word) < cutoff) {
                continue;
            }
            double score = ratio(candidate, word);
            if (score < cutoff) {
                continue;
            }
            if (score > bestScore || (score == bestScore && candidate.compareTo(best) > 0)) {
                best = candidate;
                bestScore = score;
            }
        }
        return Optional.ofNullable(best);
    }

    private static double realQuickRatio(String a, String b) {
        int total = a.length() + b.length();
        return total == 0 ? 1.0 : 2.0 * Math.min(a.length(), b.length()) / total;
    }

    private static double quickRatio(String a, String b) {
        Map<Character, Integer> available = new HashMap<>();
        for (char c : b.toCharArray()) {
            available.merge(c, 1, Integer::sum);
        }
        int matches = 0;
        for (char c : a.toCharArray()) {
            Integer left = available.get(c);
            if (left != null && left > 0) {
                available.put(c, left - 1);
                matches++;
            }
        }
        int total = a.length() + b.length();
        return total == 0 ? 1.0 : 2.0 * matches / total;
    }

    /** Suma de los bloques de get_matching_blocks(). */
    private static int matchingCharacters(String a, String b) {
        Map<Character, List<Integer>> b2j = new HashMap<>();
        for (int j = 0; j < b.length(); j++) {
            b2j.computeIfAbsent(b.charAt(j), c -> new ArrayList<>()).add(j);
        }
        int matched = 0;
        Deque<int[]> queue = new ArrayDeque<>();
        queue.push(new int[] {0, a.length(), 0, b.length()});
        while (!queue.isEmpty()) {
            int[] range = queue.pop();
            int alo = range[0], ahi = range[1], blo = range[2], bhi = range[3];
            int[] match = longestMatch(a, b, b2j, alo, ahi, blo, bhi);
            int i = match[0], j = match[1], k = match[2];
            if (k > 0) {
                matched += k;
                if (alo < i && blo < j) {
                    queue.push(new int[] {alo, i, blo, j});
                }
                if (i + k < ahi && j + k < bhi) {
                    queue.push(new int[] {i + k, ahi, j + k, bhi});
                }
            }
        }
        return matched;
    }

    /** find_longest_match: el bloque comun mas largo; a igual largo, el que empieza antes en a y luego en b. */
    private static int[] longestMatch(String a, String b, Map<Character, List<Integer>> b2j,
                                      int alo, int ahi, int blo, int bhi) {
        int besti = alo, bestj = blo, bestsize = 0;
        Map<Integer, Integer> j2len = new HashMap<>();
        for (int i = alo; i < ahi; i++) {
            Map<Integer, Integer> newj2len = new HashMap<>();
            for (int j : b2j.getOrDefault(a.charAt(i), List.of())) {
                if (j < blo) {
                    continue;
                }
                if (j >= bhi) {
                    break;
                }
                int k = j2len.getOrDefault(j - 1, 0) + 1;
                newj2len.put(j, k);
                if (k > bestsize) {
                    besti = i - k + 1;
                    bestj = j - k + 1;
                    bestsize = k;
                }
            }
            j2len = newj2len;
        }
        // Sin junk, difflib igual intenta extender el bloque hacia ambos lados.
        while (besti > alo && bestj > blo && a.charAt(besti - 1) == b.charAt(bestj - 1)) {
            besti--;
            bestj--;
            bestsize++;
        }
        while (besti + bestsize < ahi && bestj + bestsize < bhi && a.charAt(besti + bestsize) == b.charAt(bestj + bestsize)) {
            bestsize++;
        }
        return new int[] {besti, bestj, bestsize};
    }
}

package io.github.simonvc89.thpc.telegram;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Objects;
import org.junit.jupiter.api.Test;

/**
 * El port debe dar exactamente lo mismo que difflib de Python. Los casos esperados se
 * generaron con Python 3.13 sobre palabras reales del catalogo, con y sin errores de
 * tipeo (resources/telegram/difflib-cases.tsv).
 */
class DifflibTest {

    private static List<String> lines(String resource) throws IOException {
        try (InputStream in = Objects.requireNonNull(DifflibTest.class.getResourceAsStream(resource))) {
            return new String(in.readAllBytes(), StandardCharsets.UTF_8).lines()
                    .filter(l -> !l.isBlank() && !l.startsWith("#"))
                    .toList();
        }
    }

    @Test
    void ratioIgualQuePython() throws IOException {
        List<String> cases = lines("/telegram/difflib-cases.tsv").stream().filter(l -> l.startsWith("ratio\t")).toList();
        assertThat(cases).hasSizeGreaterThan(100);
        for (String line : cases) {
            String[] f = line.split("\t", -1);
            assertThat(Difflib.ratio(f[1], f[2])).as("ratio(%s, %s)", f[1], f[2]).isEqualTo(Double.parseDouble(f[3]));
        }
    }

    @Test
    void closeMatchIgualQuePython() throws IOException {
        List<String> vocabulary = lines("/telegram/vocabulary.txt");
        List<String> cases = lines("/telegram/difflib-cases.tsv").stream().filter(l -> l.startsWith("close\t")).toList();
        assertThat(cases).hasSizeGreaterThan(50);
        for (String line : cases) {
            String[] f = line.split("\t", -1);
            assertThat(Difflib.closeMatch(f[1], vocabulary, 0.75).orElse("")).as("closeMatch(%s)", f[1]).isEqualTo(f[2]);
        }
    }

    @Test
    void casosBorde() {
        assertThat(Difflib.ratio("", "")).isEqualTo(1.0);
        assertThat(Difflib.ratio("abc", "")).isEqualTo(0.0);
        assertThat(Difflib.closeMatch("zzzz", List.of("catan", "azul"), 0.75)).isEmpty();
    }
}

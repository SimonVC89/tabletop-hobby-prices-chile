package io.github.simonvc89.thpc.telegram;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

/** Mismos casos que scraper/tests/test_telegram_watchlist.py (busqueda y paginacion). */
class BotSearchTest {

    private static BotSearch.Item item(String name, Integer price) {
        return BotSearch.Item.of(UUID.nameUUIDFromBytes(name.getBytes(StandardCharsets.UTF_8)), name, 3, price);
    }

    private static BotSearch.Item item(String name) {
        return item(name, 10000);
    }

    private static final List<BotSearch.Item> CATALOG = List.of(
            item("Catan"),
            item("Catan Navegantes"),
            item("Catan: Navegantes de Catan Exp. 5-6 Jug."),
            item("Catan Ciudades Y Caballeros Ampliación 5-6 Jugadores"),
            item("Catan Junior", null),
            item("Cares Of Pandora"),
            item("Arkham Horror LCG"),
            item("Arkham Horror LCG: El Círculo Roto exp Campaña"),
            item("Arkham Horror LCG La Fiesta del Valle de la Cicuta exp. campaña"),
            item("Arkham Horror LCG La Fiesta del Valle de la Cicuta exp. investigadores"),
            item("Terraforming Mars: Expedición Ares"));

    private static List<String> names(String query) {
        return BotSearch.matchCatalog(CATALOG, BotSearch.terms(query)).stream().map(BotSearch.Item::name).toList();
    }

    @Test
    void codigoCortoTocable() {
        String code = BotSearch.codeOf(UUID.fromString("c827edbb-d4df-4055-9e04-a95ed0070531"));
        assertThat(code).isEqualTo("c827edbb");
        // Telegram solo convierte en enlace un comando con letras, numeros y guion bajo.
        assertThat("/seguir_" + code).matches("/seguir_[a-z0-9]+");
    }

    @Test
    void cadaPalabraEsUnPrefijo() {
        assertThat(names("catan nav")).contains("Catan Navegantes");
        assertThat(names("ark hor")).contains("Arkham Horror LCG");
    }

    @Test
    void noBuscaEnMedioDeUnaPalabra() {
        // "ares" no debe traer "Cares".
        assertThat(names("ares")).containsExactly("Terraforming Mars: Expedición Ares");
    }

    @Test
    void ignoraTildesMayusculasYOrden() {
        assertThat(names("CÍRCULO arkham")).containsExactly("Arkham Horror LCG: El Círculo Roto exp Campaña");
        assertThat(names("navegantes catan")).isEqualTo(names("catan navegantes"));
    }

    @Test
    void entiendeSinonimos() {
        var both = List.of("Catan: Navegantes de Catan Exp. 5-6 Jug.", "Catan Ciudades Y Caballeros Ampliación 5-6 Jugadores");
        assertThat(names("catan expansion 5 6 jugadores")).containsExactlyInAnyOrderElementsOf(both);
        assertThat(names("catan ampliacion 5-6 jug")).containsExactlyInAnyOrderElementsOf(both);
    }

    @Test
    void ordenDeLosResultados() {
        List<String> result = names("catan");
        assertThat(result.getFirst()).isEqualTo("Catan");                       // nombre exacto primero
        assertThat(result.getLast()).isEqualTo("Catan Junior");                  // sin stock al final
        assertThat(result.indexOf("Catan Navegantes"))                           // nombres cortos antes
                .isLessThan(result.indexOf("Catan Ciudades Y Caballeros Ampliación 5-6 Jugadores"));
    }

    @Test
    void sinCoincidencias() {
        assertThat(names("zzzzqqq")).isEmpty();
    }

    @Test
    void corrigeErroresDeTipeo() {
        assertThat(BotSearch.correctTerms(CATALOG, List.of("catna"))).containsExactly("catan");
        assertThat(BotSearch.correctTerms(CATALOG, List.of("arkam", "horror"))).containsExactly("arkham", "horror");
    }

    @Test
    void noCorrigeLoQueYaExisteNiLasPalabrasCortas() {
        assertThat(BotSearch.correctTerms(CATALOG, List.of("nav"))).containsExactly("nav");               // prefijo de "navegantes"
        assertThat(BotSearch.correctTerms(CATALOG, List.of("ark"))).containsExactly("ark");               // muy corta
        assertThat(BotSearch.correctTerms(CATALOG, List.of("qwertyuiop"))).containsExactly("qwertyuiop"); // nada se parece
    }

    @Test
    void laBusquedaAvisaSiCorrigio() {
        BotSearch.Result result = BotSearch.search(CATALOG, "catna navegantes");
        assertThat(result.corrected()).isEqualTo("catan navegantes");
        assertThat(result.matches()).extracting(BotSearch.Item::name).contains("Catan Navegantes");
    }

    @Test
    void palabrasParaAcotarSeparanLosResultados() {
        var arkham = BotSearch.matchCatalog(CATALOG, List.of("arkham"));
        List<String> words = BotSearch.narrowingWords(arkham, List.of("arkham"), 5);
        assertThat(words).contains("campaña");                      // con tilde, como en los nombres
        assertThat(words).doesNotContain("arkham", "horror");       // ya estan en la busqueda
    }

    @Test
    void palabrasParaAcotarNoRepitenSingularYPlural() {
        var matches = List.of(item("X uno investigador"), item("X dos investigadores"), item("X tres investigadores"),
                item("X cuatro mazo"));
        List<String> words = BotSearch.narrowingWords(matches, List.of("x"), 5);
        assertThat(words.contains("investigador") && words.contains("investigadores")).isFalse();
    }

    @Test
    void elComandoDePaginacionIdaYVuelta() {
        String command = BotSearch.moreCommand(2, List.of("arkham", "horror", "lcg")).orElseThrow();
        assertThat(command).isEqualTo("/mas_2_arkham_horror_lcg");
        var parsed = BotSearch.parseMoreCommand(command.substring("/mas_".length())).orElseThrow();
        assertThat(parsed.page()).isEqualTo(2);
        assertThat(parsed.terms()).containsExactly("arkham", "horror", "lcg");
    }

    @Test
    void paginacionConBusquedaDemasiadoLargaNoOfreceEnlace() {
        assertThat(BotSearch.moreCommand(2, List.of("terraforming", "mars", "expedicion", "ares", "descubrimiento", "crisis")))
                .isEmpty();
        assertThat(BotSearch.MAX_COMMAND_LENGTH).isEqualTo(60);
    }

    @ParameterizedTest
    @ValueSource(strings = {"x_arkham", "1_catan", "0_catan", "2", "2_", "_catan", "", "99999999999_catan"})
    void comandosDePaginacionInvalidos(String rest) {
        assertThat(BotSearch.parseMoreCommand(rest)).isEmpty();
    }

    @Test
    void ordinalesYSinonimos() {
        assertThat(BotSearch.canonical("2da")).isEqualTo("ord2");
        assertThat(BotSearch.canonical("segunda")).isEqualTo("ord2");
        assertThat(BotSearch.canonical("exp")).isEqualTo("expansion");
        assertThat(BotSearch.canonical("catan")).isEqualTo("catan");
    }

    @Test
    void preciosConPuntoDeMiles() {
        assertThat(BotSearch.clp(24990)).isEqualTo("$24.990");
        assertThat(BotSearch.clp(1234567)).isEqualTo("$1.234.567");
        assertThat(BotSearch.clp(990)).isEqualTo("$990");
    }
}

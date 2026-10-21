package io.github.simonvc89.thpc.telegram;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Instant;
import org.junit.jupiter.api.Test;

class BotStatusTest {

    // 21-10-2026 17:16 en Chile (UTC-3 en horario de verano).
    private static final Instant NOW = Instant.parse("2026-10-21T20:16:00Z");

    @Test
    void momentosRelativosEnHoraDeChile() {
        assertThat(BotStatus.when(Instant.parse("2026-10-21T09:05:00Z"), NOW)).isEqualTo("hoy a las 06:05");
        assertThat(BotStatus.when(Instant.parse("2026-10-21T01:45:00Z"), NOW)).isEqualTo("ayer a las 22:45");
        assertThat(BotStatus.when(Instant.parse("2026-10-19T12:00:00Z"), NOW)).isEqualTo("el 19-10 a las 09:00");
    }

    @Test
    void proximaRevisionDelScraper() {
        assertThat(BotStatus.nextRun(NOW)).isEqualTo("hoy a las 19:17");
        assertThat(BotStatus.nextRun(Instant.parse("2026-10-21T07:00:00Z"))).isEqualTo("hoy a las 05:17");  // 04:00 Chile
        assertThat(BotStatus.nextRun(Instant.parse("2026-10-22T00:30:00Z"))).isEqualTo("mañana a las 05:17"); // 21:30 Chile
    }

    @Test
    void mensajeCompleto() {
        String text = new BotStatus(Instant.parse("2026-10-21T09:05:00Z"), 100, 0, true, 4,
                Instant.parse("2026-10-20T01:45:00Z")).message(NOW);
        assertThat(text)
                .contains("Precios revisados hoy a las 06:05. Próxima revisión: hoy a las 19:17.")
                .contains("Ofertas vigentes: 100 juegos (0 destacadas)")
                .contains("Último resumen enviado: el 19-10 a las 22:45.")
                .contains("Tu resumen de ofertas: activo.")
                .contains("Sigues 4 juegos: usa /siguiendo para verlos.")
                .contains("unos días de silencio son normales");
    }

    @Test
    void sinResumenSinSuscripcionYSinJuegos() {
        String text = new BotStatus(null, 1, 1, false, 0, null).message(NOW);
        assertThat(text)
                .contains("Precios revisados todavía sin datos")
                .contains("1 juego (1 destacada)")
                .contains("Último resumen enviado: todavía ninguno.")
                .contains("pausado (actívalo con /start)")
                .contains("No sigues juegos todavía");
    }
}

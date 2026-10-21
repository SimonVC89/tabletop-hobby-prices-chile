package io.github.simonvc89.thpc.telegram;

import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * Respuesta de /estado: muestra que la app sigue al dia aunque el bot lleve dias sin
 * escribir (el resumen solo sale cuando hay ofertas nuevas). Logica pura: los datos
 * los junta {@link BotCommands}.
 *
 * @param lastUpdated ultima vez que se vio un precio (null si la base esta vacia)
 * @param gamesOnSale juegos con al menos una oferta (no ofertas: dos tiendas cuentan una vez)
 * @param destacadas  juegos con una oferta de 50% o mas
 * @param lastDigest  ultimo resumen de ofertas enviado (null si nunca salio uno)
 */
record BotStatus(Instant lastUpdated, int gamesOnSale, int destacadas, boolean subscribed, long follows,
                 Instant lastDigest) {

    static final ZoneId CHILE = ZoneId.of("America/Santiago");
    /**
     * Horas a las que cron-job.org lanza el scraper (ver .github/workflows/scraper.yml),
     * en hora de Chile. Cada corrida tarda cerca de una hora.
     */
    static final List<LocalTime> SCRAPER_RUNS = List.of(LocalTime.of(5, 17), LocalTime.of(19, 17));
    static final String OFFERS_URL = "https://thpc.vercel.app/ofertas";

    private static final DateTimeFormatter HOUR = DateTimeFormatter.ofPattern("HH:mm");
    private static final DateTimeFormatter DAY = DateTimeFormatter.ofPattern("dd-MM");

    String message(Instant now) {
        StringBuilder text = new StringBuilder("📊 Estado de Tabletop Hobby Prices\n");
        text.append("• Precios revisados ")
                .append(lastUpdated == null ? "todavía sin datos" : when(lastUpdated, now))
                .append(". Próxima revisión: ").append(nextRun(now)).append(".\n");
        text.append("• Ofertas vigentes: ").append(gamesOnSale).append(gamesOnSale == 1 ? " juego" : " juegos")
                .append(" (").append(destacadas).append(destacadas == 1 ? " destacada" : " destacadas")
                .append("). Ver todas: ").append(OFFERS_URL).append('\n');
        text.append("• Último resumen enviado: ")
                .append(lastDigest == null ? "todavía ninguno" : when(lastDigest, now)).append(".\n");
        text.append("• Tu resumen de ofertas: ")
                .append(subscribed ? "activo." : "pausado (actívalo con /start).").append('\n');
        text.append(follows == 0
                ? "• No sigues juegos todavía: prueba con /seguir catan."
                : "• Sigues " + follows + (follows == 1 ? " juego" : " juegos") + ": usa /siguiendo para verlos.");
        text.append("\n\nEl resumen solo llega cuando aparecen ofertas nuevas, así que unos días de silencio son normales.");
        return text.toString();
    }

    /** "hoy a las 06:05", "ayer a las 22:45" o "el 19-10 a las 22:45", en hora de Chile. */
    static String when(Instant moment, Instant now) {
        ZonedDateTime t = moment.atZone(CHILE);
        LocalDate today = now.atZone(CHILE).toLocalDate();
        String hour = t.format(HOUR);
        if (t.toLocalDate().equals(today)) {
            return "hoy a las " + hour;
        }
        if (t.toLocalDate().equals(today.minusDays(1))) {
            return "ayer a las " + hour;
        }
        return "el " + t.format(DAY) + " a las " + hour;
    }

    /** Proxima corrida programada del scraper: "hoy a las 19:17" o "mañana a las 05:17". */
    static String nextRun(Instant now) {
        ZonedDateTime local = now.atZone(CHILE);
        for (LocalTime run : SCRAPER_RUNS) {
            if (local.toLocalTime().isBefore(run)) {
                return "hoy a las " + run.format(HOUR);
            }
        }
        return "mañana a las " + SCRAPER_RUNS.getFirst().format(HOUR);
    }
}

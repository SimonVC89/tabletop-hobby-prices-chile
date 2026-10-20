package io.github.simonvc89.thpc.telegram;

/**
 * Textos del bot. Los mismos que tenia la version de Python, salvo el aviso de demora:
 * con el webhook las respuestas son inmediatas.
 */
final class BotTexts {

    static final int MAX_FOLLOWS = 20;
    /** Mismo umbral que los avisos de juegos seguidos (scraper/src/telegram_watchlist.py). */
    static final int WATCH_DROP_PCT = 5;

    static final String HELP = """
            Comandos disponibles:
            /start - suscribirte al resumen de ofertas (mañana y tarde, solo cuando hay ofertas nuevas)
            /stop - pausar el resumen (puedes volver con /start). No afecta a los juegos que sigues
            /seguir <juego> - avisarte cuando un juego baje de precio o vuelva a tener stock
            /siguiendo - ver los juegos que sigues
            /dar_de_baja - baja total y permanente de todo aviso (también borra tu lista). \
            Por ahora no se puede reactivar.
            /ayuda - este mensaje""";

    static final String START = "Listo, quedaste suscrito al resumen de ofertas: te escribo en la mañana y en la tarde, "
            + "solo cuando hay ofertas nuevas. También puedes seguir juegos puntuales con /seguir. "
            + "Usa /ayuda para ver más opciones.";

    static final String START_OPTED_OUT = "Te diste de baja total anteriormente, así que por ahora no puedo "
            + "volver a suscribirte.";

    static final String STOP = "Listo, te diste de baja del resumen de ofertas. Puedes volver a suscribirte cuando "
            + "quieras con /start. Los juegos que sigues con /seguir se mantienen: usa /siguiendo para verlos.";

    static final String OPTED_OUT = "Listo, diste de baja total: no vas a recibir ningún aviso más y borré tu lista "
            + "de juegos.";

    static final String FOLLOW_OPTED_OUT = "Te diste de baja total anteriormente, así que no puedo seguir juegos "
            + "para ti.";

    static final String FOLLOW_HOW = """
            Dime qué juego quieres seguir, por ejemplo:
            /seguir catan

            Te aviso cuando baje de precio o vuelva a tener stock.""";

    static final String INVALID_MORE = "Ese comando no es válido. Usa /seguir seguido del nombre del juego.";
    static final String NO_MORE = "No hay más resultados para esa búsqueda.";
    static final String INVALID_CODE = "Ese código no es válido. Usa /seguir seguido del nombre del juego.";
    static final String CODE_NOT_FOUND = "No encontré ese juego (puede que ya no esté disponible). Busca de nuevo "
            + "con /seguir y el nombre.";
    static final String INVALID_UNFOLLOW_CODE = "Ese código no es válido. Mira tu lista con /siguiendo.";
    static final String NOT_FOLLOWING = "No estabas siguiendo ese juego. Mira tu lista con /siguiendo.";
    static final String EMPTY_LIST = "Todavía no sigues ningún juego. Prueba con /seguir y el nombre, por ejemplo: "
            + "/seguir catan";
    static final String MAX_REACHED = "Ya sigues " + MAX_FOLLOWS + " juegos, que es el máximo. Deja de seguir alguno "
            + "con /siguiendo para agregar otro.";
    static final String UNKNOWN = "No entendí ese comando. Envía /ayuda para ver las opciones.";

    private BotTexts() {
    }
}

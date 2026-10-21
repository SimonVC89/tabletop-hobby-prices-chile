package io.github.simonvc89.thpc.telegram;

import static io.github.simonvc89.thpc.telegram.BotSearch.MAX_OPTIONS;
import static io.github.simonvc89.thpc.telegram.BotSearch.clp;
import static io.github.simonvc89.thpc.telegram.BotSearch.codeOf;

import io.github.simonvc89.thpc.meta.MetaQueries;
import io.github.simonvc89.thpc.offer.OfferQueries;
import io.github.simonvc89.thpc.offer.OfferResponse;
import io.github.simonvc89.thpc.offer.OfferTier;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Responde los comandos del bot. Misma logica que scraper/src/poll_telegram_commands.py
 * y telegram_watchlist.py; aca cada mensaje llega solo (webhook) en vez de en tandas.
 *
 * <p>Cada comando se resuelve sin estado entre mensajes: /seguir responde con opciones
 * que son comandos tocables (/seguir_c827edbb) y la paginacion lleva la busqueda dentro
 * del comando (/mas_2_arkham_horror_lcg).
 */
@Service
public class BotCommands {

    private final BotRepository repo;
    private final BotCatalog catalog;
    private final MetaQueries meta;
    private final OfferQueries offers;

    BotCommands(BotRepository repo, BotCatalog catalog, MetaQueries meta, OfferQueries offers) {
        this.repo = repo;
        this.catalog = catalog;
        this.meta = meta;
        this.offers = offers;
    }

    /**
     * Procesa un mensaje y devuelve la respuesta, o vacio si no hay que responder (mensaje
     * repetido o chat bloqueado). Marcar el mensaje y aplicar el comando van en la misma
     * transaccion.
     */
    @Transactional
    public Optional<String> handle(long updateId, String chatId, String text) {
        if (!repo.markProcessed(updateId) || repo.isBlocked(chatId)) {
            return Optional.empty();
        }
        return reply(chatId, text.strip().toLowerCase(Locale.ROOT));
    }

    Optional<String> reply(String chatId, String text) {
        int space = text.indexOf(' ');
        String command = space < 0 ? text : text.substring(0, space);
        String args = space < 0 ? "" : text.substring(space + 1);
        // En grupos Telegram agrega el nombre del bot: "/seguir@MiBot catan".
        int at = command.indexOf('@');
        if (at >= 0) {
            command = command.substring(0, at);
        }

        return switch (command) {
            case "/ayuda" -> Optional.of(BotTexts.HELP);
            case "/start" -> Optional.of(start(chatId));
            case "/stop" -> {
                repo.unsubscribe(chatId);
                yield Optional.of(BotTexts.STOP);
            }
            case "/dar_de_baja" -> {
                repo.optOutPermanently(chatId);
                yield Optional.of(BotTexts.OPTED_OUT);
            }
            case "/siguiendo" -> Optional.of(following(chatId));
            case "/estado" -> Optional.of(status(chatId));
            case "/seguir" -> follow(chatId, args);
            default -> {
                if (command.startsWith("/seguir_")) {
                    yield followCode(chatId, command.substring("/seguir_".length()));
                }
                if (command.startsWith("/mas_")) {
                    yield more(chatId, command.substring("/mas_".length()));
                }
                if (command.startsWith("/dejar_")) {
                    yield Optional.of(unfollow(chatId, command.substring("/dejar_".length())));
                }
                yield Optional.of(BotTexts.UNKNOWN);
            }
        };
    }

    /** /estado: que la app sigue al dia, aunque el resumen lleve dias sin salir. */
    private String status(String chatId) {
        List<OfferResponse> current = offers.currentOffers();
        int games = (int) current.stream().map(OfferResponse::productId).distinct().count();
        int destacadas = (int) current.stream()
                .filter(o -> o.tier() == OfferTier.DESTACADA)
                .map(OfferResponse::productId)
                .distinct()
                .count();
        return new BotStatus(meta.lastUpdated(), games, destacadas, repo.isSubscribed(chatId),
                repo.countFollows(chatId), repo.lastDigest().orElse(null)).message(Instant.now());
    }

    private String start(String chatId) {
        if (repo.subscriber(chatId).map(BotRepository.ChatState::optedOutPermanently).orElse(false)) {
            return BotTexts.START_OPTED_OUT;
        }
        repo.subscribe(chatId);
        return BotTexts.START;
    }

    /** Registra el chat y devuelve el rechazo si ya no se le puede seguir juegos. */
    private Optional<String> refusal(String chatId) {
        return repo.touchChat(chatId).optedOutPermanently() ? Optional.of(BotTexts.FOLLOW_OPTED_OUT) : Optional.empty();
    }

    private Optional<String> follow(String chatId, String rawQuery) {
        Optional<String> refusal = refusal(chatId);
        if (refusal.isPresent()) {
            return refusal;
        }
        String query = rawQuery.strip();
        if (query.isEmpty()) {
            return Optional.of(BotTexts.FOLLOW_HOW);
        }

        BotSearch.Result found = BotSearch.search(catalog.items(), query);
        List<BotSearch.Item> matches = found.matches();
        if (matches.isEmpty()) {
            return Optional.of("No encontré juegos con «" + query + "». Prueba con menos palabras o revisa cómo se escribe.");
        }
        // Con un error de tipeo corregido se pide confirmar, aunque haya una sola coincidencia.
        if (matches.size() == 1 && found.corrected() == null) {
            return Optional.of(addToList(chatId, matches.getFirst().id(), matches.getFirst().name()));
        }

        String header = found.corrected() != null
                ? "No encontré «" + query + "». ¿Quisiste decir «" + found.corrected() + "»? Toca el juego que quieres seguir:"
                : "Encontré " + matches.size() + " juegos con «" + query + "». Toca el que quieres seguir:";
        return Optional.of(header + "\n" + options(matches.subList(0, Math.min(MAX_OPTIONS, matches.size())))
                + "\n" + footer(matches, found.terms(), 1, true));
    }

    /** Otra pagina de resultados: /mas_&lt;pagina&gt;_&lt;palabras separadas por _&gt;. */
    private Optional<String> more(String chatId, String rest) {
        Optional<String> refusal = refusal(chatId);
        if (refusal.isPresent()) {
            return refusal;
        }
        Optional<BotSearch.MoreRequest> parsed = BotSearch.parseMoreCommand(rest);
        if (parsed.isEmpty()) {
            return Optional.of(BotTexts.INVALID_MORE);
        }
        int page = parsed.get().page();
        List<String> terms = parsed.get().terms();

        List<BotSearch.Item> matches = BotSearch.matchCatalog(catalog.items(), terms);
        int start = (page - 1) * MAX_OPTIONS;
        if (start >= matches.size()) {
            return Optional.of(BotTexts.NO_MORE);
        }
        int end = Math.min(start + MAX_OPTIONS, matches.size());
        String header = "Juegos con «" + String.join(" ", terms) + "»: " + (start + 1) + "-" + end + " de "
                + matches.size() + ". Toca el que quieres seguir:";
        return Optional.of(header + "\n" + options(matches.subList(start, end)) + "\n" + footer(matches, terms, page, false));
    }

    private Optional<String> followCode(String chatId, String code) {
        Optional<String> refusal = refusal(chatId);
        if (refusal.isPresent()) {
            return refusal;
        }
        if (!BotSearch.isValidCode(code)) {
            return Optional.of(BotTexts.INVALID_CODE);
        }
        List<BotRepository.Product> products = repo.productsByCode(code);
        if (products.size() != 1) {
            return Optional.of(BotTexts.CODE_NOT_FOUND);
        }
        return Optional.of(addToList(chatId, products.getFirst().id(), products.getFirst().name()));
    }

    private String addToList(String chatId, UUID productId, String name) {
        if (repo.isFollowing(chatId, productId)) {
            return "Ya sigues " + name + ". Mira tu lista con /siguiendo.";
        }
        if (repo.countFollows(chatId) >= BotTexts.MAX_FOLLOWS) {
            return BotTexts.MAX_REACHED;
        }
        Optional<BotRepository.Offer> offer = repo.bestOffer(productId);
        repo.follow(chatId, productId, offer);

        String status = offer
                .map(o -> "Hoy el mejor precio es " + clp(o.price()) + " en " + o.storeName() + ". Te aviso cuando baje al menos "
                        + BotTexts.WATCH_DROP_PCT + "% más o si se agota y vuelve.")
                .orElse("Hoy está agotado en las tiendas que sigo. Te aviso cuando vuelva a tener stock.");
        return "⭐ Ahora sigues " + name + ".\n" + status + "\nVe tu lista con /siguiendo.";
    }

    private String following(String chatId) {
        List<BotRepository.WatchedGame> games = repo.watched(chatId);
        if (games.isEmpty()) {
            return BotTexts.EMPTY_LIST;
        }
        List<String> lines = new ArrayList<>();
        lines.add("Sigues " + games.size() + " de " + BotTexts.MAX_FOLLOWS + " juegos posibles:");
        for (BotRepository.WatchedGame g : games) {
            String status = g.bestPrice() != null ? clp(g.bestPrice()) : "agotado";
            lines.add("\n" + g.name() + " (" + status + ")\nDejar de seguir: /dejar_" + codeOf(g.productId()));
        }
        return String.join("\n", lines);
    }

    private String unfollow(String chatId, String code) {
        if (!BotSearch.isValidCode(code)) {
            return BotTexts.INVALID_UNFOLLOW_CODE;
        }
        return repo.unfollow(chatId, code).map(name -> "Listo, dejé de seguir " + name + ".").orElse(BotTexts.NOT_FOLLOWING);
    }

    static String options(List<BotSearch.Item> items) {
        List<String> lines = new ArrayList<>();
        for (BotSearch.Item m : items) {
            String price = m.price() != null ? "desde " + clp(m.price()) : "agotado";
            lines.add("\n" + m.name() + " (" + price + ")\n/seguir_" + codeOf(m.id()));
        }
        return String.join("\n", lines);
    }

    /** Pie de la lista: cuantos hay, como ver mas y que palabras agregar para acotar. */
    static String footer(List<BotSearch.Item> matches, List<String> terms, int page, boolean hints) {
        int total = matches.size();
        if (total <= MAX_OPTIONS) {
            return "";
        }
        int start = (page - 1) * MAX_OPTIONS;
        int shownTo = Math.min(start + MAX_OPTIONS, total);
        List<String> parts = new ArrayList<>();
        parts.add("\nMostrando " + (start + 1) + "-" + shownTo + " de " + total + ".");
        if (shownTo < total) {
            BotSearch.moreCommand(page + 1, terms).ifPresent(link -> parts.add("Ver los siguientes: " + link));
        }
        if (hints) {
            List<String> words = BotSearch.narrowingWords(matches, terms, 5);
            if (!words.isEmpty()) {
                parts.add("Para acotar, agrega una palabra: " + String.join(", ", words));
            }
        }
        return String.join("\n", parts);
    }
}

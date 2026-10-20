package io.github.simonvc89.thpc.telegram;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * Anti-abuso: como maximo {@link #LIMIT} comandos por chat cada {@link #WINDOW}; los
 * demas se descartan sin responder (igual que el limite por tanda del polling). En
 * memoria: si el servidor se reinicia, los contadores parten de cero, y para un bot
 * de este tamano basta.
 */
@Component
class ChatRateLimiter {

    static final int LIMIT = 10;
    static final Duration WINDOW = Duration.ofMinutes(1);
    /** Si hay muchos chats distintos, se olvidan las ventanas ya vencidas. */
    private static final int MAX_TRACKED_CHATS = 10_000;

    private record Window(Instant start, int count) {
    }

    private final Map<String, Window> windows = new ConcurrentHashMap<>();
    private final Clock clock;

    @Autowired
    ChatRateLimiter() {
        this(Clock.systemUTC());
    }

    ChatRateLimiter(Clock clock) {
        this.clock = clock;
    }

    boolean allow(String chatId) {
        Instant now = clock.instant();
        if (windows.size() > MAX_TRACKED_CHATS) {
            windows.values().removeIf(w -> w.start().plus(WINDOW).isBefore(now));
        }
        Window w = windows.compute(chatId, (id, current) ->
                current == null || !current.start().plus(WINDOW).isAfter(now)
                        ? new Window(now, 1)
                        : new Window(current.start(), current.count() + 1));
        return w.count() <= LIMIT;
    }
}

package io.github.simonvc89.thpc.telegram;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;

class ChatRateLimiterTest {

    private final AtomicReference<Instant> now = new AtomicReference<>(Instant.parse("2026-10-20T12:00:00Z"));
    private final ChatRateLimiter limiter = new ChatRateLimiter(new Clock() {
        @Override
        public ZoneOffset getZone() {
            return ZoneOffset.UTC;
        }

        @Override
        public Clock withZone(ZoneId zone) {
            return this;
        }

        @Override
        public Instant instant() {
            return now.get();
        }
    });

    @Test
    void permiteHastaElLimiteYDescartaElResto() {
        for (int i = 0; i < ChatRateLimiter.LIMIT; i++) {
            assertThat(limiter.allow("1")).isTrue();
        }
        assertThat(limiter.allow("1")).isFalse();
    }

    @Test
    void cadaChatTieneSuPropioLimite() {
        for (int i = 0; i < ChatRateLimiter.LIMIT; i++) {
            limiter.allow("1");
        }
        assertThat(limiter.allow("2")).isTrue();
    }

    @Test
    void alPasarLaVentanaVuelveAPermitir() {
        for (int i = 0; i <= ChatRateLimiter.LIMIT; i++) {
            limiter.allow("1");
        }
        now.set(now.get().plus(ChatRateLimiter.WINDOW));
        assertThat(limiter.allow("1")).isTrue();
    }
}

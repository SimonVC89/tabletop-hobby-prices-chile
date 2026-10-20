package io.github.simonvc89.thpc;

import java.util.List;
import java.util.Set;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Configuracion propia de la API (prefijo {@code thpc} en application.yml).
 *
 * @param manualStores        tiendas que solo se actualizan a mano porque bloquean los
 *                            servidores en la nube; misma lista que scraper/src/manual_stores.py
 * @param corsAllowedOrigins  origenes desde los que un navegador puede llamar a la API
 *                            (el frontend local y, publicado, su dominio)
 * @param telegram            bot de Telegram (webhook)
 */
@ConfigurationProperties("thpc")
public record ThpcProperties(Set<String> manualStores, List<String> corsAllowedOrigins, Telegram telegram) {

    public ThpcProperties {
        manualStores = manualStores == null ? Set.of() : Set.copyOf(manualStores);
        corsAllowedOrigins = corsAllowedOrigins == null ? List.of() : List.copyOf(corsAllowedOrigins);
        telegram = telegram == null ? new Telegram("", "") : telegram;
    }

    /**
     * @param botToken      token del bot (BotFather); sin el, no se envian respuestas
     * @param webhookSecret secreto que Telegram manda en cada llamada al webhook; sin el,
     *                      el webhook rechaza todo
     */
    public record Telegram(String botToken, String webhookSecret) {

        public Telegram {
            botToken = botToken == null ? "" : botToken;
            webhookSecret = webhookSecret == null ? "" : webhookSecret;
        }

        @Override
        public String toString() {
            // Nunca imprimir el token ni el secreto (por ejemplo en logs de configuracion).
            return "Telegram[botToken=" + (botToken.isEmpty() ? "" : "***") + ", webhookSecret="
                    + (webhookSecret.isEmpty() ? "" : "***") + "]";
        }
    }
}

package io.github.simonvc89.thpc.telegram;

import io.github.simonvc89.thpc.ThpcProperties;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

/**
 * Cliente minimo de la API de Telegram: solo sendMessage. Sin libreria de terceros,
 * igual que scraper/src/telegram.py.
 *
 * <p>El token va en la URL de Telegram, asi que los errores se registran sin el
 * mensaje de la excepcion (que la incluye).
 */
@Component
class HttpTelegramClient implements TelegramClient {

    private static final Logger log = LoggerFactory.getLogger(HttpTelegramClient.class);

    private final RestClient rest;
    private final String token;

    // RestClient.builder() directo: en Spring Boot 4 el bean RestClient.Builder viene en
    // un modulo aparte (spring-boot-restclient) que no hace falta solo para esto.
    HttpTelegramClient(ThpcProperties properties) {
        this.rest = RestClient.builder().baseUrl("https://api.telegram.org").build();
        this.token = properties.telegram().botToken();
    }

    @Override
    public boolean sendMessage(String chatId, String text) {
        if (token.isEmpty()) {
            log.warn("Sin TELEGRAM_BOT_TOKEN: no se envia la respuesta");
            return false;
        }
        try {
            rest.post()
                    .uri("/bot{token}/sendMessage", token)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(Map.of("chat_id", chatId, "text", text, "disable_web_page_preview", true))
                    .retrieve()
                    .toBodilessEntity();
            return true;
        } catch (RestClientResponseException e) {
            // 403 = el usuario bloqueo el bot; el resumen de Python ya maneja ese caso.
            log.warn("Telegram rechazo un mensaje: HTTP {}", e.getStatusCode().value());
            return false;
        } catch (RestClientException e) {
            log.warn("No se pudo contactar a Telegram: {}", e.getClass().getSimpleName());
            return false;
        }
    }
}

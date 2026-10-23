package io.github.simonvc89.thpc.telegram;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.github.simonvc89.thpc.ThpcProperties;
import io.swagger.v3.oas.annotations.Hidden;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

/**
 * Webhook del bot: Telegram llama aqui con cada mensaje apenas se escribe (en vez del
 * polling cada ~3 h desde GitHub Actions). Se registra con setWebhook pasando un
 * secret_token, que Telegram devuelve en cada llamada en un header: sin ese secreto
 * la llamada se rechaza, asi nadie mas puede hacerse pasar por Telegram.
 */
@RestController
@Hidden // Solo para Telegram (exige un secreto): no va en la documentacion publica.
public class TelegramWebhookController {

    static final String SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token";
    private static final Logger log = LoggerFactory.getLogger(TelegramWebhookController.class);

    /** Lo que se usa de un Update de Telegram; el resto de campos se ignora. */
    @JsonIgnoreProperties(ignoreUnknown = true)
    record Update(@JsonProperty("update_id") long updateId, Message message) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    record Message(Chat chat, String text) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    record Chat(long id) {
    }

    private final byte[] secret;
    private final BotCommands commands;
    private final ChatRateLimiter rateLimiter;
    private final TelegramClient telegram;

    TelegramWebhookController(ThpcProperties properties, BotCommands commands, ChatRateLimiter rateLimiter,
                              TelegramClient telegram) {
        this.secret = properties.telegram().webhookSecret().getBytes(StandardCharsets.UTF_8);
        this.commands = commands;
        this.rateLimiter = rateLimiter;
        this.telegram = telegram;
    }

    @PostMapping("/api/telegram/webhook")
    public ResponseEntity<Void> receive(@RequestHeader(value = SECRET_HEADER, required = false) String header,
                                        @RequestBody Update update) {
        if (!validSecret(header)) {
            return ResponseEntity.status(401).build();
        }
        // Solo mensajes de texto (comandos); fotos, ediciones, etc. no se responden.
        if (update.message() == null || update.message().text() == null || update.message().chat() == null) {
            return ResponseEntity.ok().build();
        }
        String chatId = String.valueOf(update.message().chat().id());
        if (!rateLimiter.allow(chatId)) {
            return ResponseEntity.ok().build();
        }
        try {
            commands.handle(update.updateId(), chatId, update.message().text())
                    .ifPresent(reply -> telegram.sendMessage(chatId, reply));
        } catch (RuntimeException e) {
            // Se responde 200 igual: un error 5xx haria que Telegram reintente el mismo
            // mensaje una y otra vez.
            log.error("Error procesando un comando del bot", e);
        }
        return ResponseEntity.ok().build();
    }

    /** Comparacion en tiempo constante; sin secreto configurado, nada es valido. */
    private boolean validSecret(String header) {
        return secret.length > 0 && header != null
                && MessageDigest.isEqual(secret, header.getBytes(StandardCharsets.UTF_8));
    }
}

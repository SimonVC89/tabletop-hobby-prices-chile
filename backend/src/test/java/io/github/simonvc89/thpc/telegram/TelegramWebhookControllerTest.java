package io.github.simonvc89.thpc.telegram;

import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(TelegramWebhookController.class)
@TestPropertySource(properties = "thpc.telegram.webhook-secret=secreto-de-prueba")
class TelegramWebhookControllerTest {

    private static final String UPDATE = """
            {"update_id": 42, "message": {"message_id": 7, "chat": {"id": 12345, "type": "private"},
             "from": {"id": 12345, "first_name": "Ana"}, "text": "/seguir catan"}}
            """;

    @Autowired
    private MockMvc mvc;

    @MockitoBean
    private BotCommands commands;

    @MockitoBean
    private ChatRateLimiter rateLimiter;

    @MockitoBean
    private TelegramClient telegram;

    @Test
    void sinSecretoSeRechaza() throws Exception {
        mvc.perform(post("/api/telegram/webhook").contentType(MediaType.APPLICATION_JSON).content(UPDATE))
                .andExpect(status().isUnauthorized());
        verify(commands, never()).handle(anyLong(), anyString(), anyString());
    }

    @Test
    void conSecretoIncorrectoSeRechaza() throws Exception {
        mvc.perform(post("/api/telegram/webhook").header(TelegramWebhookController.SECRET_HEADER, "otro")
                        .contentType(MediaType.APPLICATION_JSON).content(UPDATE))
                .andExpect(status().isUnauthorized());
        verify(commands, never()).handle(anyLong(), anyString(), anyString());
    }

    @Test
    void conSecretoProcesaYResponde() throws Exception {
        given(rateLimiter.allow("12345")).willReturn(true);
        given(commands.handle(42, "12345", "/seguir catan")).willReturn(Optional.of("respuesta"));

        mvc.perform(post("/api/telegram/webhook").header(TelegramWebhookController.SECRET_HEADER, "secreto-de-prueba")
                        .contentType(MediaType.APPLICATION_JSON).content(UPDATE))
                .andExpect(status().isOk());
        verify(telegram).sendMessage("12345", "respuesta");
    }

    @Test
    void sobreElLimiteNoSeProcesa() throws Exception {
        given(rateLimiter.allow("12345")).willReturn(false);

        mvc.perform(post("/api/telegram/webhook").header(TelegramWebhookController.SECRET_HEADER, "secreto-de-prueba")
                        .contentType(MediaType.APPLICATION_JSON).content(UPDATE))
                .andExpect(status().isOk());
        verify(commands, never()).handle(anyLong(), anyString(), anyString());
    }

    @Test
    void unErrorAlProcesarIgualResponde200ParaQueTelegramNoReintente() throws Exception {
        given(rateLimiter.allow("12345")).willReturn(true);
        given(commands.handle(42, "12345", "/seguir catan")).willThrow(new IllegalStateException("base caida"));

        mvc.perform(post("/api/telegram/webhook").header(TelegramWebhookController.SECRET_HEADER, "secreto-de-prueba")
                        .contentType(MediaType.APPLICATION_JSON).content(UPDATE))
                .andExpect(status().isOk());
        verify(telegram, never()).sendMessage(anyString(), anyString());
    }

    @Test
    void mensajesSinTextoSeIgnoran() throws Exception {
        mvc.perform(post("/api/telegram/webhook").header(TelegramWebhookController.SECRET_HEADER, "secreto-de-prueba")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"update_id\": 43, \"edited_message\": {\"chat\": {\"id\": 1}, \"text\": \"hola\"}}"))
                .andExpect(status().isOk());
        verify(commands, never()).handle(anyLong(), anyString(), anyString());
    }
}

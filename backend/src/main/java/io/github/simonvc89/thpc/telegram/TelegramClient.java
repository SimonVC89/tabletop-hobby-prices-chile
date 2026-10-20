package io.github.simonvc89.thpc.telegram;

/** Envio de mensajes por la API de Telegram (interfaz para poder reemplazarlo en las pruebas). */
public interface TelegramClient {

    /** Envia un mensaje; falso si Telegram no lo acepto (por ejemplo, el usuario bloqueo el bot). */
    boolean sendMessage(String chatId, String text);
}

package io.github.simonvc89.thpc.telegram;

import jakarta.persistence.EntityManager;
import jakarta.persistence.Tuple;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.stereotype.Repository;

/**
 * Tablas del bot (telegram_subscribers, telegram_watchlist, telegram_bot_state) en SQL
 * nativo; mismas consultas que scraper/src/telegram_subscribers.py y telegram_watchlist.py.
 * Las transacciones las abre {@link BotCommands}.
 */
@Repository
@SuppressWarnings("unchecked") // createNativeQuery devuelve listas sin tipo
class BotRepository {

    /** Estado del chat que importa para responder. */
    record ChatState(boolean optedOutPermanently, boolean blocked) {
    }

    record WatchedGame(UUID productId, String name, Integer bestPrice) {
    }

    record Offer(int price, String storeName) {
    }

    record Product(UUID id, String name) {
    }

    private final EntityManager em;

    BotRepository(EntityManager em) {
        this.em = em;
    }

    /**
     * Marca el mensaje como procesado. Falso si ya se proceso (Telegram reenvia un
     * mensaje si no recibe respuesta a tiempo): asi no se responde dos veces.
     */
    boolean markProcessed(long updateId) {
        List<Object> updated = em.createNativeQuery("""
                        insert into telegram_bot_state (key, value) values ('last_update_id', :id)
                        on conflict (key) do update set value = excluded.value
                        where telegram_bot_state.value::bigint < excluded.value::bigint
                        returning value
                        """)
                .setParameter("id", String.valueOf(updateId))
                .getResultList();
        return !updated.isEmpty();
    }

    boolean isBlocked(String chatId) {
        List<Object> rows = em.createNativeQuery("select is_blocked from telegram_subscribers where chat_id = :chat")
                .setParameter("chat", chatId)
                .getResultList();
        return !rows.isEmpty() && (Boolean) rows.getFirst();
    }

    Optional<ChatState> subscriber(String chatId) {
        List<Tuple> rows = em.createNativeQuery(
                        "select opted_out_permanently, is_blocked from telegram_subscribers where chat_id = :chat", Tuple.class)
                .setParameter("chat", chatId)
                .getResultList();
        return rows.stream().findFirst()
                .map(r -> new ChatState((Boolean) r.get("opted_out_permanently"), (Boolean) r.get("is_blocked")));
    }

    /** Registra el chat si es nuevo (sin suscribirlo al resumen) y devuelve su estado. */
    ChatState touchChat(String chatId) {
        Tuple r = (Tuple) em.createNativeQuery("""
                        insert into telegram_subscribers (chat_id, is_active, last_command_at)
                        values (:chat, false, now())
                        on conflict (chat_id) do update set last_command_at = now()
                        returning opted_out_permanently, is_blocked
                        """, Tuple.class)
                .setParameter("chat", chatId)
                .getSingleResult();
        return new ChatState((Boolean) r.get("opted_out_permanently"), (Boolean) r.get("is_blocked"));
    }

    void subscribe(String chatId) {
        em.createNativeQuery("""
                        insert into telegram_subscribers (chat_id, is_active, last_command_at)
                        values (:chat, true, now())
                        on conflict (chat_id) do update set is_active = true, last_command_at = now()
                        """)
                .setParameter("chat", chatId)
                .executeUpdate();
    }

    void unsubscribe(String chatId) {
        em.createNativeQuery("""
                        insert into telegram_subscribers (chat_id, is_active, last_command_at)
                        values (:chat, false, now())
                        on conflict (chat_id) do update set is_active = false, last_command_at = now()
                        """)
                .setParameter("chat", chatId)
                .executeUpdate();
    }

    /** Baja total: sin resumen, marcada como permanente y sin juegos seguidos. */
    void optOutPermanently(String chatId) {
        em.createNativeQuery("""
                        insert into telegram_subscribers (chat_id, is_active, opted_out_permanently, last_command_at)
                        values (:chat, false, true, now())
                        on conflict (chat_id) do update set
                            is_active = false, opted_out_permanently = true, last_command_at = now()
                        """)
                .setParameter("chat", chatId)
                .executeUpdate();
        em.createNativeQuery("delete from telegram_watchlist where chat_id = :chat")
                .setParameter("chat", chatId)
                .executeUpdate();
    }

    long countFollows(String chatId) {
        return ((Number) em.createNativeQuery("select count(*) from telegram_watchlist where chat_id = :chat")
                .setParameter("chat", chatId)
                .getSingleResult()).longValue();
    }

    boolean isFollowing(String chatId, UUID productId) {
        return !em.createNativeQuery("select 1 from telegram_watchlist where chat_id = :chat and product_id = :product")
                .setParameter("chat", chatId)
                .setParameter("product", productId)
                .getResultList().isEmpty();
    }

    /** Mejor precio con stock del producto y su tienda. */
    Optional<Offer> bestOffer(UUID productId) {
        List<Tuple> rows = em.createNativeQuery("""
                        select cp.price_clp, s.name as store_name
                        from current_prices cp join stores s on s.id = cp.store_id
                        where cp.product_id = :product and cp.in_stock
                        order by cp.price_clp limit 1
                        """, Tuple.class)
                .setParameter("product", productId)
                .getResultList();
        return rows.stream().findFirst()
                .map(r -> new Offer(((Number) r.get("price_clp")).intValue(), (String) r.get("store_name")));
    }

    /** Sigue un juego; sin oferta (agotado) no hay precio de referencia y queda sin stock. */
    void follow(String chatId, UUID productId, Optional<Offer> offer) {
        // El null va escrito en el SQL: un parametro null sin tipo, Postgres lo rechaza.
        var query = offer.isPresent()
                ? em.createNativeQuery("""
                        insert into telegram_watchlist (chat_id, product_id, ref_price, in_stock)
                        values (:chat, :product, :ref, true)
                        """).setParameter("ref", offer.get().price())
                : em.createNativeQuery("""
                        insert into telegram_watchlist (chat_id, product_id, ref_price, in_stock)
                        values (:chat, :product, null, false)
                        """);
        query.setParameter("chat", chatId).setParameter("product", productId).executeUpdate();
    }

    List<WatchedGame> watched(String chatId) {
        List<Tuple> rows = em.createNativeQuery("""
                        select p.id, p.canonical_name, b.min_price
                        from telegram_watchlist w
                        join products p on p.id = w.product_id
                        left join (
                            select product_id, min(price_clp) as min_price
                            from current_prices where in_stock group by product_id
                        ) b on b.product_id = w.product_id
                        where w.chat_id = :chat
                        order by w.created_at
                        """, Tuple.class)
                .setParameter("chat", chatId)
                .getResultList();
        return rows.stream()
                .map(r -> new WatchedGame((UUID) r.get("id"), (String) r.get("canonical_name"),
                        r.get("min_price") == null ? null : ((Number) r.get("min_price")).intValue()))
                .toList();
    }

    /** Deja de seguir el juego cuyo id empieza con el codigo; devuelve su nombre si lo seguia. */
    Optional<String> unfollow(String chatId, String code) {
        List<Object> rows = em.createNativeQuery("""
                        delete from telegram_watchlist w using products p
                        where w.product_id = p.id and w.chat_id = :chat and p.id::text like :prefix
                        returning p.canonical_name
                        """)
                .setParameter("chat", chatId)
                .setParameter("prefix", code + "%")
                .getResultList();
        return rows.stream().findFirst().map(String.class::cast);
    }

    /** Productos visibles cuyo id empieza con el codigo (deberia ser uno). */
    List<Product> productsByCode(String code) {
        List<Tuple> rows = em.createNativeQuery("""
                        select id, canonical_name from products
                        where id::text like :prefix and hidden_at is null and merged_into is null
                          and category = 'board_game'
                        """, Tuple.class)
                .setParameter("prefix", code + "%")
                .getResultList();
        return rows.stream().map(r -> new Product((UUID) r.get("id"), (String) r.get("canonical_name"))).toList();
    }
}

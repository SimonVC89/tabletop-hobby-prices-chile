package io.github.simonvc89.thpc.meta;

import jakarta.persistence.EntityManager;
import java.time.Instant;
import org.springframework.stereotype.Repository;

/**
 * Agregados del catalogo en SQL nativo: no son entidades, son conteos y maximos.
 * Los usa /api/meta; el frontend los muestra en Inicio y en el pie.
 */
@Repository
public class MetaQueries {

    private final EntityManager em;

    public MetaQueries(EntityManager em) {
        this.em = em;
    }

    /**
     * Ultimo scraping con datos. Se usa last_seen_at de los listings y no la ultima
     * fila de price_history, que solo guarda cambios de precio.
     */
    public Instant lastUpdated() {
        return (Instant) em.createNativeQuery("select max(last_seen_at) from product_listings", Instant.class)
                .getSingleResult();
    }

    /** Juegos de mesa visibles, con o sin stock (los fusionados quedan ocultos). */
    public long totalGames() {
        Number count = (Number) em.createNativeQuery(
                        "select count(*) from products where hidden_at is null and category = 'board_game'")
                .getSingleResult();
        return count.longValue();
    }
}

package io.github.simonvc89.thpc.pricedrop;

import jakarta.persistence.EntityManager;
import jakarta.persistence.Tuple;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Repository;

@Repository
public class PriceDropQueries {

    // price_history guarda solo cambios: la ultima fila de un listing ES su ultimo
    // cambio. Hay baja si esa fila es reciente, tiene stock y es mas barata que la
    // anterior, tambien con stock (volver a tener stock no es una baja).
    private static final String CANDIDATES_SQL = """
            with ranked as (
                select ph.listing_id, ph.price_clp, ph.in_stock, ph.scraped_at,
                       row_number() over (partition by ph.listing_id order by ph.scraped_at desc) as rn
                from price_history ph
                join product_listings pl on pl.id = ph.listing_id and pl.is_active
            )
            select p.id as product_id, p.canonical_name, p.image_url, s.name as store_name, pl.url,
                   prev.price_clp as previous_price, last.price_clp as price, last.scraped_at as changed_at
            from ranked last
            join ranked prev on prev.listing_id = last.listing_id and prev.rn = 2
            join product_listings pl on pl.id = last.listing_id
            join products p on p.id = pl.product_id
            join stores s on s.id = pl.store_id and s.active
            where last.rn = 1
              and last.scraped_at > now() - make_interval(hours => :hours)
              and last.in_stock and prev.in_stock and last.price_clp < prev.price_clp
              and p.hidden_at is null and p.merged_into is null and p.category = 'board_game'
            """;

    private final EntityManager em;

    public PriceDropQueries(EntityManager em) {
        this.em = em;
    }

    @SuppressWarnings("unchecked") // createNativeQuery devuelve una List sin tipo
    public List<PriceDropSelector.Candidate> candidates() {
        List<Tuple> rows = em.createNativeQuery(CANDIDATES_SQL, Tuple.class)
                .setParameter("hours", PriceDropSelector.WINDOW_HOURS)
                .getResultList();
        return rows.stream()
                .map(r -> new PriceDropSelector.Candidate(
                        (UUID) r.get("product_id"),
                        (String) r.get("canonical_name"),
                        (String) r.get("image_url"),
                        (String) r.get("store_name"),
                        (String) r.get("url"),
                        ((Number) r.get("previous_price")).intValue(),
                        ((Number) r.get("price")).intValue(),
                        (Instant) r.get("changed_at")))
                .toList();
    }
}

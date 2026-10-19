package io.github.simonvc89.thpc.offer;

import jakarta.persistence.EntityManager;
import jakarta.persistence.Tuple;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.OptionalDouble;
import java.util.UUID;
import org.springframework.stereotype.Repository;

@Repository
public class OfferQueries {

    // Una fila por tienda y juego: si la tienda lo publica en dos paginas, la mas
    // barata. La mediana sale de product_price_stats (un precio por tienda).
    private static final String CANDIDATES_SQL = """
            select distinct on (cp.product_id, cp.store_id)
                   p.id as product_id, p.canonical_name, p.image_url,
                   s.name as store_name, pl.url, cp.price_clp,
                   round(pps.median_price_clp)::int as median_price, pps.store_count,
                   pps.min_price_clp, pps.max_price_clp
            from current_prices cp
            join product_price_stats pps on pps.product_id = cp.product_id
            join products p on p.id = cp.product_id
            join stores s on s.id = cp.store_id
            join product_listings pl on pl.id = cp.listing_id
            where pps.store_count >= :minStores and cp.in_stock
              and cp.price_clp < pps.median_price_clp
              and p.hidden_at is null and p.category = 'board_game'
            order by cp.product_id, cp.store_id, cp.price_clp
            """;

    private final EntityManager em;

    public OfferQueries(EntityManager em) {
        this.em = em;
    }

    /** Ofertas de hoy (20% o mas bajo la mediana), de mayor a menor descuento. */
    @SuppressWarnings("unchecked") // createNativeQuery devuelve una List sin tipo
    public List<OfferResponse> currentOffers() {
        List<Tuple> rows = em.createNativeQuery(CANDIDATES_SQL, Tuple.class)
                .setParameter("minStores", OfferRules.MIN_STORES_FOR_MEDIAN)
                .getResultList();

        List<OfferResponse> offers = new ArrayList<>();
        for (Tuple row : rows) {
            int price = intValue(row, "price_clp");
            int median = intValue(row, "median_price");
            long storeCount = ((Number) row.get("store_count")).longValue();
            OptionalDouble pct = OfferRules.discountPct(price, median, storeCount);
            if (pct.isEmpty() || pct.getAsDouble() < OfferRules.OFFER_THRESHOLD) {
                continue;
            }
            offers.add(new OfferResponse(
                    (UUID) row.get("product_id"),
                    (String) row.get("canonical_name"),
                    (String) row.get("image_url"),
                    (String) row.get("store_name"),
                    (String) row.get("url"),
                    price,
                    median,
                    intValue(row, "min_price_clp"),
                    intValue(row, "max_price_clp"),
                    pct.getAsDouble(),
                    storeCount,
                    OfferRules.tier(pct.getAsDouble())));
        }
        offers.sort(Comparator.comparingDouble(OfferResponse::discountPct).reversed());
        return offers;
    }

    private static int intValue(Tuple row, String column) {
        return ((Number) row.get(column)).intValue();
    }
}

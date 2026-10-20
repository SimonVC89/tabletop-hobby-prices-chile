package io.github.simonvc89.thpc.product;

import io.github.simonvc89.thpc.offer.OfferRules;
import jakarta.persistence.EntityManager;
import jakarta.persistence.Tuple;
import java.time.Instant;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalDouble;
import java.util.UUID;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

/** Consultas de productos en SQL nativo: catalogo, ficha, historial y similitud de titulos. */
@Repository
@Transactional(readOnly = true)
@SuppressWarnings("unchecked") // createNativeQuery devuelve listas sin tipo
public class ProductQueries {

    // Todos los juegos visibles, tambien los agotados en todas las tiendas: de esos
    // se informa el ultimo precio visto y cuando (last_seen_at del listing, porque
    // price_history guarda solo cambios).
    private static final String SUMMARIES_SQL = """
            with best as (
                select distinct on (cp.product_id)
                       cp.product_id, cp.price_clp, s.name as store_name
                from current_prices cp join stores s on s.id = cp.store_id
                where cp.in_stock
                order by cp.product_id, cp.price_clp
            ),
            last_seen as (
                select distinct on (pl.product_id)
                       pl.product_id, ph.price_clp, pl.last_seen_at as scraped_at
                from product_listings pl
                join lateral (
                    select price_clp from price_history
                    where listing_id = pl.id order by scraped_at desc limit 1
                ) ph on true
                order by pl.product_id, pl.last_seen_at desc, ph.price_clp
            )
            select p.id, p.canonical_name, p.image_url,
                   coalesce(pps.store_count, 0) as store_count,
                   b.price_clp as best_price, b.store_name as best_store,
                   round(pps.median_price_clp)::int as median_price,
                   ls.price_clp as last_price, ls.scraped_at as last_seen_at
            from products p
            left join best b on b.product_id = p.id
            left join last_seen ls on ls.product_id = p.id
            left join product_price_stats pps on pps.product_id = p.id
            where p.hidden_at is null and p.category = 'board_game'
            """;

    private static final String DETAIL_SQL = """
            select p.canonical_name, p.image_url, p.description, p.description_source,
                   round(pps.median_price_clp)::int as median_price,
                   pps.min_price_clp, pps.max_price_clp, pps.store_count
            from products p left join product_price_stats pps on pps.product_id = p.id
            where p.id = :id
            """;

    // Un listing por tienda: el activo mas barato con stock. Si la tienda ya no lo
    // publica, su ultimo precio visto, sin stock. Las tiendas excluidas no se listan.
    // El desempate final (mismo juego en dos paginas iguales) evita un resultado al azar.
    private static final String LISTINGS_SQL = """
            with latest as (
                select distinct on (ph.listing_id) ph.listing_id, ph.price_clp, ph.in_stock
                from price_history ph join product_listings pl on pl.id = ph.listing_id
                where pl.product_id = :id
                order by ph.listing_id, ph.scraped_at desc
            )
            select distinct on (pl.store_id)
                   s.id as store_id, s.name as store_name, pl.url, l.price_clp,
                   (l.in_stock and pl.is_active) as in_stock, pl.last_seen_at
            from product_listings pl
            join latest l on l.listing_id = pl.id
            join stores s on s.id = pl.store_id
            where pl.product_id = :id and s.active
            order by pl.store_id, pl.is_active desc, (l.in_stock and pl.is_active) desc, l.price_clp,
                     pl.last_seen_at desc, pl.url
            """;

    // Dias en hora de Chile: una corrida de las 23:10 hora de Chile es de ese dia.
    private static final String HISTORY_SQL = """
            select pl.id as listing_id, s.id as store_id, s.name as store_name, pl.is_active,
                   (pl.last_seen_at at time zone 'America/Santiago')::date as seen_day,
                   (ph.scraped_at at time zone 'America/Santiago')::date as day, ph.price_clp, ph.in_stock
            from price_history ph
            join product_listings pl on pl.id = ph.listing_id
            join stores s on s.id = pl.store_id
            where pl.product_id = :id
            order by pl.id, ph.scraped_at
            """;

    // Similitud coseno (1 - distancia de pgvector) entre el embedding promedio de los
    // titulos de cada juego y el del juego pedido.
    private static final String SIMILARITY_SQL = """
            with target as (
                select avg(title_embedding) as e from product_listings
                where product_id = :id and title_embedding is not null
            )
            select pl.product_id, 1 - (avg(pl.title_embedding) <=> (select e from target)) as score
            from product_listings pl
            where pl.product_id is not null and pl.title_embedding is not null
              and (select e from target) is not null
            group by pl.product_id
            """;

    private final EntityManager em;

    public ProductQueries(EntityManager em) {
        this.em = em;
    }

    public List<ProductSummary> summaries() {
        List<Tuple> rows = em.createNativeQuery(SUMMARIES_SQL, Tuple.class).getResultList();
        return rows.stream().map(r -> {
            Integer best = integer(r, "best_price");
            Integer median = integer(r, "median_price");
            int storeCount = integer(r, "store_count");
            OptionalDouble discount = OfferRules.discountPct(best, median, storeCount);
            boolean soldOut = best == null;
            return new ProductSummary(
                    (UUID) r.get("id"),
                    (String) r.get("canonical_name"),
                    (String) r.get("image_url"),
                    storeCount,
                    best,
                    (String) r.get("best_store"),
                    median,
                    discount.isPresent() ? discount.getAsDouble() : null,
                    soldOut ? integer(r, "last_price") : null,
                    soldOut ? (Instant) r.get("last_seen_at") : null);
        }).toList();
    }

    public Optional<ProductDetailResponse> detail(UUID id) {
        List<Tuple> found = em.createNativeQuery(DETAIL_SQL, Tuple.class).setParameter("id", id).getResultList();
        if (found.isEmpty()) {
            return Optional.empty();
        }
        Tuple p = found.getFirst();
        Integer median = integer(p, "median_price");
        ProductDetailResponse.Stats stats = median == null ? null : new ProductDetailResponse.Stats(
                median, integer(p, "min_price_clp"), integer(p, "max_price_clp"), integer(p, "store_count"));

        List<Tuple> listingRows = em.createNativeQuery(LISTINGS_SQL, Tuple.class).setParameter("id", id).getResultList();
        List<ProductDetailResponse.Listing> listings = listingRows.stream()
                .map(l -> new ProductDetailResponse.Listing(
                        (UUID) l.get("store_id"),
                        (String) l.get("store_name"),
                        (String) l.get("url"),
                        integer(l, "price_clp"),
                        (Boolean) l.get("in_stock"),
                        (Instant) l.get("last_seen_at")))
                .sorted((a, b) -> Integer.compare(a.price(), b.price()))
                .toList();

        String description = (String) p.get("description");
        return Optional.of(new ProductDetailResponse(
                id,
                (String) p.get("canonical_name"),
                (String) p.get("image_url"),
                description,
                description == null ? null : (String) p.get("description_source"),
                listings,
                stats));
    }

    public PriceHistoryResponse history(UUID id) {
        List<Tuple> rows = em.createNativeQuery(HISTORY_SQL, Tuple.class).setParameter("id", id).getResultList();
        List<PriceHistoryBuilder.Row> history = rows.stream()
                .map(r -> new PriceHistoryBuilder.Row(
                        (UUID) r.get("listing_id"),
                        (UUID) r.get("store_id"),
                        (String) r.get("store_name"),
                        (Boolean) r.get("is_active"),
                        localDate(r.get("seen_day")),
                        localDate(r.get("day")),
                        integer(r, "price_clp"),
                        (Boolean) r.get("in_stock")))
                .toList();
        return new PriceHistoryResponse(id,
                PriceHistoryBuilder.build(history, lastScrapeDay(), PriceHistoryBuilder.CHANGES_ONLY_FROM));
    }

    /** Similitud de cada juego con embedding respecto del juego pedido; vacio si este no tiene. */
    public Map<UUID, Double> similarityScores(UUID id) {
        List<Tuple> rows = em.createNativeQuery(SIMILARITY_SQL, Tuple.class).setParameter("id", id).getResultList();
        Map<UUID, Double> scores = new HashMap<>();
        for (Tuple r : rows) {
            scores.put((UUID) r.get("product_id"), ((Number) r.get("score")).doubleValue());
        }
        return scores;
    }

    private LocalDate lastScrapeDay() {
        return localDate(em.createNativeQuery(
                        "select (max(last_seen_at) at time zone 'America/Santiago')::date from product_listings")
                .getSingleResult());
    }

    private static Integer integer(Tuple row, String column) {
        Object value = row.get(column);
        return value == null ? null : ((Number) value).intValue();
    }

    private static LocalDate localDate(Object value) {
        return value instanceof java.sql.Date date ? date.toLocalDate() : (LocalDate) value;
    }
}

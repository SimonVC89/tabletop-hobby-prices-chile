package io.github.simonvc89.thpc.product;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * Los ~6.000 juegos visibles en memoria, recargados cada {@link #TTL}. Los precios
 * cambian dos veces al dia (cron), asi que no vale la pena consultar la base en
 * cada busqueda; a cambio, tras una corrida del cron la API puede tardar hasta
 * {@link #TTL} en mostrar los precios nuevos.
 */
@Component
public class ProductCatalog {

    static final Duration TTL = Duration.ofMinutes(10);

    private record Snapshot(List<ProductSummary> products, Map<UUID, ProductSummary> byId, Instant loadedAt) {
    }

    private final ProductQueries queries;
    private final Clock clock;
    private volatile Snapshot snapshot;

    @Autowired
    public ProductCatalog(ProductQueries queries) {
        this(queries, Clock.systemUTC());
    }

    ProductCatalog(ProductQueries queries, Clock clock) {
        this.queries = queries;
        this.clock = clock;
    }

    public List<ProductSummary> all() {
        return current().products();
    }

    public Map<UUID, ProductSummary> byId() {
        return current().byId();
    }

    public Optional<ProductSummary> find(UUID id) {
        return Optional.ofNullable(current().byId().get(id));
    }

    private Snapshot current() {
        Snapshot s = snapshot;
        if (s == null || s.loadedAt().plus(TTL).isBefore(clock.instant())) {
            synchronized (this) {
                s = snapshot;
                if (s == null || s.loadedAt().plus(TTL).isBefore(clock.instant())) {
                    List<ProductSummary> products = queries.summaries();
                    s = new Snapshot(products,
                            products.stream().collect(Collectors.toUnmodifiableMap(ProductSummary::id, Function.identity())),
                            clock.instant());
                    snapshot = s;
                }
            }
        }
        return s;
    }
}

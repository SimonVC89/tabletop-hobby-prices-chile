package io.github.simonvc89.thpc.store;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.util.UUID;
import org.hibernate.annotations.Immutable;

/**
 * Tienda que se sigue. Solo lectura: las tiendas las crea y actualiza el scraper.
 * {@code active = false} es una tienda excluida (bloquea el acceso automatizado).
 */
@Entity
@Immutable
@Table(name = "stores")
public class Store {

    @Id
    private UUID id;

    @Column(nullable = false)
    private String name;

    @Column(name = "base_url", nullable = false)
    private String baseUrl;

    @Column(nullable = false)
    private boolean active;

    protected Store() {
    }

    public UUID getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getBaseUrl() {
        return baseUrl;
    }

    public boolean isActive() {
        return active;
    }
}

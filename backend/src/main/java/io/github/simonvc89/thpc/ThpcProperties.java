package io.github.simonvc89.thpc;

import java.util.Set;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Configuracion propia de la API (prefijo {@code thpc} en application.yml).
 *
 * @param manualStores tiendas que solo se actualizan a mano porque bloquean los
 *                     servidores en la nube; misma lista que scraper/src/manual_stores.py
 */
@ConfigurationProperties("thpc")
public record ThpcProperties(Set<String> manualStores) {

    public ThpcProperties {
        manualStores = manualStores == null ? Set.of() : Set.copyOf(manualStores);
    }
}

package io.github.simonvc89.thpc;

import java.util.List;
import java.util.Set;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Configuracion propia de la API (prefijo {@code thpc} en application.yml).
 *
 * @param manualStores        tiendas que solo se actualizan a mano porque bloquean los
 *                            servidores en la nube; misma lista que scraper/src/manual_stores.py
 * @param corsAllowedOrigins  origenes desde los que un navegador puede llamar a la API
 *                            (el frontend local y, publicado, su dominio)
 */
@ConfigurationProperties("thpc")
public record ThpcProperties(Set<String> manualStores, List<String> corsAllowedOrigins) {

    public ThpcProperties {
        manualStores = manualStores == null ? Set.of() : Set.copyOf(manualStores);
        corsAllowedOrigins = corsAllowedOrigins == null ? List.of() : List.copyOf(corsAllowedOrigins);
    }
}

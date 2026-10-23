package io.github.simonvc89.thpc.store;

import io.github.simonvc89.thpc.ThpcProperties;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/stores")
@Tag(name = "Tiendas", description = "Tiendas chilenas que se revisan")
public class StoreController {

    private final StoreRepository stores;
    private final ThpcProperties properties;

    public StoreController(StoreRepository stores, ThpcProperties properties) {
        this.stores = stores;
        this.properties = properties;
    }

    /** Todas las tiendas, tambien las excluidas (el frontend decide que mostrar), por nombre. */
    @GetMapping
    @Transactional(readOnly = true)
    @Operation(summary = "Tiendas",
            description = "Todas las tiendas, ordenadas por nombre, con sus productos activos. status: daily "
                    + "(se revisa sola dos veces al día), manual (bloquea servidores en la nube y se actualiza "
                    + "a mano) o excluded (bloquea el acceso automatizado; se dejó de revisar).")
    public List<StoreResponse> list() {
        Map<UUID, Long> listings = stores.countActiveListings().stream()
                .collect(Collectors.toMap(StoreRepository.ListingCount::getStoreId,
                        StoreRepository.ListingCount::getActiveListings));
        return stores.findAllByOrderByNameAsc().stream()
                .map(s -> new StoreResponse(s.getId(), s.getName(), s.getBaseUrl(),
                        listings.getOrDefault(s.getId(), 0L), status(s)))
                .toList();
    }

    private StoreStatus status(Store store) {
        if (!store.isActive()) {
            return StoreStatus.EXCLUDED;
        }
        return properties.manualStores().contains(store.getName()) ? StoreStatus.MANUAL : StoreStatus.DAILY;
    }
}

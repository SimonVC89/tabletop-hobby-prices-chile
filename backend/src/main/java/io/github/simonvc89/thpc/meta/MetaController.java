package io.github.simonvc89.thpc.meta;

import io.github.simonvc89.thpc.store.StoreRepository;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/meta")
public class MetaController {

    private final MetaQueries queries;
    private final StoreRepository stores;

    public MetaController(MetaQueries queries, StoreRepository stores) {
        this.queries = queries;
        this.stores = stores;
    }

    @GetMapping
    @Transactional(readOnly = true)
    public MetaResponse get() {
        return new MetaResponse(queries.lastUpdated(), queries.totalGames(), stores.countByActiveTrue());
    }
}

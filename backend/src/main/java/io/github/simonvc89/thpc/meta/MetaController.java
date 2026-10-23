package io.github.simonvc89.thpc.meta;

import io.github.simonvc89.thpc.store.StoreRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/meta")
@Tag(name = "Estado", description = "Si los datos están al día y cuánto hay en el catálogo")
public class MetaController {

    private final MetaQueries queries;
    private final StoreRepository stores;

    public MetaController(MetaQueries queries, StoreRepository stores) {
        this.queries = queries;
        this.stores = stores;
    }

    @GetMapping
    @Transactional(readOnly = true)
    @Operation(summary = "Resumen del catálogo",
            description = "Última vez que se revisó un precio, juegos de mesa visibles (con o sin stock) "
                    + "y tiendas que se siguen (sin contar las excluidas).")
    public MetaResponse get() {
        return new MetaResponse(queries.lastUpdated(), queries.totalGames(), stores.countByActiveTrue());
    }
}

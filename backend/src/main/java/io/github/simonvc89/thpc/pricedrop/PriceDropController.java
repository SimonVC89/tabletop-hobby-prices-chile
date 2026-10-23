package io.github.simonvc89.thpc.pricedrop;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.List;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/price-drops")
@Tag(name = "Ofertas")
public class PriceDropController {

    private final PriceDropQueries queries;

    public PriceDropController(PriceDropQueries queries) {
        this.queries = queries;
    }

    @GetMapping
    @Transactional(readOnly = true)
    @Operation(summary = "Bajaron esta semana",
            description = "Juegos con stock cuyo precio bajó 5% o más en alguna tienda en los últimos 7 días y "
                    + "sigue bajo (si volvió a subir, ya no sale; volver a tener stock no cuenta). Uno por juego, "
                    + "su mayor baja, de mayor a menor, hasta 12; changedAt dice cuándo bajó. No siempre es oferta: "
                    + "a veces el juego solo vuelve a su precio normal.")
    public List<PriceDropResponse> list() {
        return PriceDropSelector.select(queries.candidates());
    }
}

package io.github.simonvc89.thpc.offer;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.List;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/offers")
@Tag(name = "Ofertas", description = "Ofertas de hoy y bajas de precio recientes")
public class OfferController {

    private final OfferQueries queries;

    public OfferController(OfferQueries queries) {
        this.queries = queries;
    }

    @GetMapping
    @Transactional(readOnly = true)
    @Operation(summary = "Ofertas de hoy",
            description = "Juegos que una tienda vende al menos 20% bajo la mediana de 3 o más tiendas con stock "
                    + "(un precio por tienda: la más barata si publica el juego dos veces). tier = destacada desde "
                    + "50%. Una oferta por tienda y juego, de mayor a menor descuento: si dos tiendas tienen el "
                    + "mismo juego en oferta, vienen las dos.")
    public List<OfferResponse> list() {
        return queries.currentOffers();
    }
}

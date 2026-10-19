package io.github.simonvc89.thpc.pricedrop;

import java.util.List;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/price-drops")
public class PriceDropController {

    private final PriceDropQueries queries;

    public PriceDropController(PriceDropQueries queries) {
        this.queries = queries;
    }

    @GetMapping
    @Transactional(readOnly = true)
    public List<PriceDropResponse> list() {
        return PriceDropSelector.select(queries.candidates());
    }
}

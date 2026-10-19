package io.github.simonvc89.thpc.offer;

import java.util.List;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/offers")
public class OfferController {

    private final OfferQueries queries;

    public OfferController(OfferQueries queries) {
        this.queries = queries;
    }

    @GetMapping
    @Transactional(readOnly = true)
    public List<OfferResponse> list() {
        return queries.currentOffers();
    }
}

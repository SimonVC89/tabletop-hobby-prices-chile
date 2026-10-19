package io.github.simonvc89.thpc.store;

import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface StoreRepository extends JpaRepository<Store, UUID> {

    /** Tiendas que se siguen (diarias o manuales); las excluidas no cuentan. */
    long countByActiveTrue();
}

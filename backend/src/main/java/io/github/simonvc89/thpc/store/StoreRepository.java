package io.github.simonvc89.thpc.store;

import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface StoreRepository extends JpaRepository<Store, UUID> {

    /** Tiendas que se siguen (diarias o manuales); las excluidas no cuentan. */
    long countByActiveTrue();

    List<Store> findAllByOrderByNameAsc();

    /** Listings activos (vistos en los ultimos scrapings) por tienda; las que no tienen no aparecen. */
    @Query(value = """
            select store_id as storeId, count(*) as activeListings
            from product_listings
            where is_active
            group by store_id
            """, nativeQuery = true)
    List<ListingCount> countActiveListings();

    interface ListingCount {
        UUID getStoreId();

        long getActiveListings();
    }
}

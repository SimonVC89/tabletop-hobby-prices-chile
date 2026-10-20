package io.github.simonvc89.thpc.offer;

import java.util.OptionalDouble;

/**
 * Reglas de oferta. El resumen de ofertas del bot de Telegram usa las mismas
 * (scraper/src/send_telegram_digest.py): si cambian aqui, hay que cambiarlas alla.
 */
public final class OfferRules {

    /** Con menos tiendas con stock la mediana no es confiable y no se calcula descuento. */
    public static final int MIN_STORES_FOR_MEDIAN = 3;
    /** Oferta: al menos este % bajo la mediana. */
    public static final double OFFER_THRESHOLD = 20;
    /** Destacada: al menos este % bajo la mediana. */
    public static final double DESTACADA_THRESHOLD = 50;

    private OfferRules() {
    }

    /**
     * Descuento de un precio respecto de la mediana, con un decimal. Vacio si no
     * hay precio o mediana, si hay menos de {@link #MIN_STORES_FOR_MEDIAN} tiendas,
     * o si el precio no esta bajo la mediana.
     */
    public static OptionalDouble discountPct(Integer price, Integer median, long storeCount) {
        if (price == null || median == null || storeCount < MIN_STORES_FOR_MEDIAN || price >= median) {
            return OptionalDouble.empty();
        }
        return OptionalDouble.of(Math.round(1000.0 * (median - price) / median) / 10.0);
    }

    public static OfferTier tier(double discountPct) {
        return discountPct >= DESTACADA_THRESHOLD ? OfferTier.DESTACADA : OfferTier.OFERTA;
    }
}

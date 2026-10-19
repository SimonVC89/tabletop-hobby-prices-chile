package io.github.simonvc89.thpc.offer;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class OfferRulesTest {

    @Test
    void calculaElDescuentoConUnDecimal() {
        // (31990 - 24990) / 31990 = 21.88 %
        assertThat(OfferRules.discountPct(24990, 31990, 5)).hasValue(21.9);
    }

    @Test
    void sinDescuentoConMenosDeTresTiendas() {
        assertThat(OfferRules.discountPct(10000, 30000, 2)).isEmpty();
    }

    @Test
    void sinDescuentoSiElPrecioNoEstaBajoLaMediana() {
        assertThat(OfferRules.discountPct(30000, 30000, 5)).isEmpty();
        assertThat(OfferRules.discountPct(35000, 30000, 5)).isEmpty();
    }

    @Test
    void sinDescuentoSiFaltaPrecioOMediana() {
        assertThat(OfferRules.discountPct(null, 30000, 5)).isEmpty();
        assertThat(OfferRules.discountPct(20000, null, 5)).isEmpty();
    }

    @Test
    void destacadaDesdeElCincuentaPorCiento() {
        assertThat(OfferRules.tier(50)).isEqualTo(OfferTier.DESTACADA);
        assertThat(OfferRules.tier(49.9)).isEqualTo(OfferTier.OFERTA);
    }
}

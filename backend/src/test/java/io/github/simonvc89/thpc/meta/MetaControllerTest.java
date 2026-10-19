package io.github.simonvc89.thpc.meta;

import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import io.github.simonvc89.thpc.store.StoreRepository;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(MetaController.class)
class MetaControllerTest {

    @Autowired
    private MockMvc mvc;

    @MockitoBean
    private MetaQueries queries;

    @MockitoBean
    private StoreRepository stores;

    @Test
    void devuelveElContratoMetaDelFrontend() throws Exception {
        given(queries.lastUpdated()).willReturn(Instant.parse("2026-10-19T16:23:00Z"));
        given(queries.totalGames()).willReturn(5999L);
        given(stores.countByActiveTrue()).willReturn(13L);

        mvc.perform(get("/api/meta"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.lastUpdated").value("2026-10-19T16:23:00Z"))
                .andExpect(jsonPath("$.totalGames").value(5999))
                .andExpect(jsonPath("$.activeStores").value(13));
    }
}

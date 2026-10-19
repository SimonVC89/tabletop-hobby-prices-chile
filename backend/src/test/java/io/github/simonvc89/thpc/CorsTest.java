package io.github.simonvc89.thpc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import io.github.simonvc89.thpc.meta.MetaController;
import io.github.simonvc89.thpc.meta.MetaQueries;
import io.github.simonvc89.thpc.store.StoreRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(MetaController.class)
class CorsTest {

    @Autowired
    private MockMvc mvc;

    @MockitoBean
    private MetaQueries queries;

    @MockitoBean
    private StoreRepository stores;

    @Test
    void elFrontendLocalPuedeLeerLaApi() throws Exception {
        mvc.perform(get("/api/meta").header("Origin", "http://localhost:5173"))
                .andExpect(status().isOk())
                .andExpect(header().string("Access-Control-Allow-Origin", "http://localhost:5173"));
    }

    @Test
    void otroSitioNoPuede() throws Exception {
        mvc.perform(get("/api/meta").header("Origin", "https://otro-sitio.example"))
                .andExpect(status().isForbidden());
    }
}

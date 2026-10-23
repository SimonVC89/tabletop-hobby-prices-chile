package io.github.simonvc89.thpc;

import io.swagger.v3.oas.models.ExternalDocumentation;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/** Datos generales de la documentacion OpenAPI (Swagger UI en /swagger-ui.html). */
@Configuration
public class OpenApiConfig {

    @Bean
    OpenAPI thpcOpenApi() {
        return new OpenAPI()
                .info(new Info()
                        .title("Tabletop Hobby Prices Chile API")
                        .version("0.1.0")
                        .description("""
                                API de solo lectura con los precios de juegos de mesa en tiendas chilenas: \
                                ofertas del día, búsqueda del catálogo, ficha de cada juego con su historial \
                                de precios por tienda y juegos relacionados.

                                Los precios se actualizan dos veces al día (05:17 y 19:17, hora de Chile). \
                                Es oferta lo que una tienda vende al menos 20% bajo la mediana de 3 o más \
                                tiendas con stock. Precios en pesos chilenos (enteros) y fechas en ISO 8601.""")
                        .contact(new Contact().name("Simón Villar").url("https://github.com/SimonVC89"))
                        .license(new License().name("MIT")
                                .url("https://github.com/SimonVC89/tabletop-hobby-prices-chile/blob/main/LICENSE")))
                .externalDocs(new ExternalDocumentation()
                        .description("Sitio que usa esta API")
                        .url("https://thpc.vercel.app"));
    }
}

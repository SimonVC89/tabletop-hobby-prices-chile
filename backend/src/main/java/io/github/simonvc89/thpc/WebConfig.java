package io.github.simonvc89.thpc;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * CORS: el frontend corre en otro origen (otro puerto en local, otro dominio
 * publicado), asi que el navegador solo lo deja leer la API si esta lo permite.
 * Lista cerrada en vez de "*": otros sitios no pueden usar la API desde el
 * navegador de sus visitantes. Solo GET, porque la API es de lectura.
 */
@Configuration
@EnableConfigurationProperties(ThpcProperties.class)
public class WebConfig implements WebMvcConfigurer {

    private final ThpcProperties properties;

    public WebConfig(ThpcProperties properties) {
        this.properties = properties;
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins(properties.corsAllowedOrigins().toArray(String[]::new))
                .allowedMethods("GET");
    }
}

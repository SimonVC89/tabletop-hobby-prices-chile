package io.github.simonvc89.thpc;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class ThpcApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(ThpcApiApplication.class, args);
    }
}

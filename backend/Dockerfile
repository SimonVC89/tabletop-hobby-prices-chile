# Imagen de la API para Render (plan gratuito: 512 MB de RAM y 0,1 CPU).

# 1) Compilacion: Maven con JDK 21. Las dependencias se descargan en una capa aparte
#    para que un cambio de codigo no las vuelva a bajar. Las pruebas corren aqui:
#    si fallan, no hay imagen y Render no despliega.
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -q -B dependency:go-offline
COPY src ./src
RUN mvn -q -B package

# 2) Ejecucion: solo el JRE y la app, con un usuario sin privilegios.
FROM eclipse-temurin:21-jre
WORKDIR /app
RUN useradd --system --uid 10001 app
COPY --from=build /app/target/thpc-api-*.jar app.jar

# CDS (Class Data Sharing): con 0,1 CPU el arranque tarda ~100 s, casi todo cargando
# clases. Un "ensayo" del arranque guarda las clases ya procesadas en app.jsa, y el
# arranque real las reutiliza. El ensayo corre sin base de datos (no hay credenciales
# al construir), asi que Hibernate no se conecta ni valida el esquema en el ensayo.
RUN java -Djarmode=tools -jar app.jar extract --destination extracted \
 && java -XX:ArchiveClassesAtExit=extracted/app.jsa -Dspring.context.exit=onRefresh \
      -Dspring.datasource.url=jdbc:postgresql://localhost/cds \
      -Dspring.jpa.hibernate.ddl-auto=none \
      -Dspring.jpa.properties.hibernate.boot.allow_jdbc_metadata_access=false \
      -Dspring.jpa.database-platform=org.hibernate.dialect.PostgreSQLDialect \
      -jar extracted/app.jar \
 && rm app.jar && chown -R app extracted

USER app
# La JVM toma como maximo el 75% de la memoria del contenedor; SerialGC usa menos
# memoria y CPU que el recolector por defecto, que en un contenedor chico no rinde.
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75 -XX:+UseSerialGC"
EXPOSE 8080
ENTRYPOINT ["java", "-XX:SharedArchiveFile=extracted/app.jsa", "-jar", "extracted/app.jar"]

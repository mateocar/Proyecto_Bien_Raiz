CREATE DATABASE IF NOT EXISTS inmobiliaria_gold
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE inmobiliaria_gold;

-- --- Dimensiones de categorización ---
CREATE TABLE IF NOT EXISTS dim_categoria_propiedad (
    id_categoria        INT AUTO_INCREMENT PRIMARY KEY,
    nombre_categoria    VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_tipo_propiedad (
    id_tipo_propiedad   INT AUTO_INCREMENT PRIMARY KEY,
    nombre_tipo         VARCHAR(80) NOT NULL UNIQUE,
    id_categoria        INT NOT NULL,
    FOREIGN KEY (id_categoria) REFERENCES dim_categoria_propiedad(id_categoria)
);

CREATE TABLE IF NOT EXISTS dim_estrato (
    id_estrato          INT AUTO_INCREMENT PRIMARY KEY,
    nivel_estrato       TINYINT NOT NULL UNIQUE,
    clasificacion       VARCHAR(50),
    descripcion         VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS dim_tipo_operacion (
    id_tipo_operacion   INT AUTO_INCREMENT PRIMARY KEY,
    nombre_operacion    VARCHAR(30) NOT NULL UNIQUE,
    es_venta            BOOLEAN NOT NULL
);

-- --- Dimensiones tiempo / características ---
CREATE TABLE IF NOT EXISTS dim_tiempo_construccion (
    id_tiempo           INT AUTO_INCREMENT PRIMARY KEY,
    anio                INT,
    decada              VARCHAR(20),
    rango_antiguedad    VARCHAR(30),
    es_desconocido      BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dim_caracteristica_fisica (
    id_caracteristica   INT AUTO_INCREMENT PRIMARY KEY,
    habitaciones        TINYINT,
    banos               DECIMAL(3,1),
    rango_tamano        VARCHAR(30),
    UNIQUE KEY uk_caract (habitaciones, banos, rango_tamano)
);

-- --- FACT_PROPIEDADES ---
CREATE TABLE IF NOT EXISTS fact_propiedades (
    id_fact                BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_estrato             INT NOT NULL,
    id_tipo_propiedad      INT NOT NULL,
    id_tipo_operacion      INT NOT NULL,
    id_tiempo              INT NOT NULL,
    id_caracteristica      INT NOT NULL,
    precio                 DECIMAL(15,2) NOT NULL,
    area_construida        DECIMAL(10,2),
    area_total             DECIMAL(12,2),
    precio_por_m2          DECIMAL(15,2),
    enlace_origen          VARCHAR(500),
    fecha_carga            DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_estrato)         REFERENCES dim_estrato(id_estrato),
    FOREIGN KEY (id_tipo_propiedad)  REFERENCES dim_tipo_propiedad(id_tipo_propiedad),
    FOREIGN KEY (id_tipo_operacion)  REFERENCES dim_tipo_operacion(id_tipo_operacion),
    FOREIGN KEY (id_tiempo)          REFERENCES dim_tiempo_construccion(id_tiempo),
    FOREIGN KEY (id_caracteristica)  REFERENCES dim_caracteristica_fisica(id_caracteristica)
);

CREATE INDEX idx_fact_tipo_op ON fact_propiedades(id_tipo_operacion);
CREATE INDEX idx_fact_precio  ON fact_propiedades(precio);
CREATE INDEX idx_fact_tiempo  ON fact_propiedades(id_tiempo);

SELECT '✅ 01_gold_base.sql ejecutado' AS resultado;
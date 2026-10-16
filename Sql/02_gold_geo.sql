USE inmobiliaria_gold;

-- --- Jerarquía geográfica ---
CREATE TABLE IF NOT EXISTS dim_pais (
    id_pais       INT AUTO_INCREMENT PRIMARY KEY,
    nombre_pais   VARCHAR(100) NOT NULL UNIQUE,
    codigo_iso    CHAR(3)
);

CREATE TABLE IF NOT EXISTS dim_departamento (
    id_departamento     INT AUTO_INCREMENT PRIMARY KEY,
    nombre_departamento VARCHAR(100) NOT NULL,
    id_pais             INT NOT NULL,
    UNIQUE KEY uk_depto (nombre_departamento, id_pais),
    FOREIGN KEY (id_pais) REFERENCES dim_pais(id_pais)
);

CREATE TABLE IF NOT EXISTS dim_ciudad (
    id_ciudad       INT AUTO_INCREMENT PRIMARY KEY,
    nombre_ciudad   VARCHAR(100) NOT NULL,
    id_departamento INT NOT NULL,
    UNIQUE KEY uk_ciudad (nombre_ciudad, id_departamento),
    FOREIGN KEY (id_departamento) REFERENCES dim_departamento(id_departamento)
);

CREATE TABLE IF NOT EXISTS dim_comuna (
    id_comuna       INT AUTO_INCREMENT PRIMARY KEY,
    cod_comuna      INT NOT NULL,
    nombre_comuna   VARCHAR(150) NOT NULL,
    tipo_zona       ENUM('Comuna','Corregimiento','Desconocido') NOT NULL DEFAULT 'Comuna',
    latitud         DECIMAL(10,7),
    longitud        DECIMAL(10,7),
    id_ciudad       INT NOT NULL,
    UNIQUE KEY uk_comuna (cod_comuna, id_ciudad),
    FOREIGN KEY (id_ciudad) REFERENCES dim_ciudad(id_ciudad)
);

CREATE INDEX idx_comuna_ciudad ON dim_comuna(id_ciudad);
CREATE INDEX idx_comuna_tipo   ON dim_comuna(tipo_zona);

CREATE TABLE IF NOT EXISTS dim_ubicacion (
    id_ubicacion    INT AUTO_INCREMENT PRIMARY KEY,
    id_comuna       INT NOT NULL,
    direccion_raw   VARCHAR(255),
    FOREIGN KEY (id_comuna) REFERENCES dim_comuna(id_comuna)
);

-- --- Agregar FK geográfica a fact_propiedades ---
ALTER TABLE fact_propiedades
    ADD COLUMN id_ubicacion INT NULL AFTER id_fact,
    ADD CONSTRAINT fk_fact_ubicacion
        FOREIGN KEY (id_ubicacion) REFERENCES dim_ubicacion(id_ubicacion);

CREATE INDEX idx_fact_ubicacion ON fact_propiedades(id_ubicacion);

-- --- DIM_FECHA ---
CREATE TABLE IF NOT EXISTS dim_fecha (
    id_fecha         INT PRIMARY KEY,
    fecha            DATE NOT NULL UNIQUE,
    anio             SMALLINT NOT NULL,
    trimestre        TINYINT  NOT NULL,
    mes              TINYINT  NOT NULL,
    nombre_mes       VARCHAR(15) NOT NULL,
    dia              TINYINT  NOT NULL,
    dia_semana       TINYINT  NOT NULL,
    nombre_dia       VARCHAR(15) NOT NULL,
    es_fin_semana    BOOLEAN  NOT NULL,
    anio_mes         CHAR(7)  NOT NULL,
    anio_trimestre   CHAR(6)  NOT NULL
);

SELECT '✅ 02_gold_geo.sql ejecutado' AS resultado;
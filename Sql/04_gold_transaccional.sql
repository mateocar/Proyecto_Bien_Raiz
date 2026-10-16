USE inmobiliaria_gold;

-- --- DIM_PROPIEDAD (puente) ---
CREATE TABLE IF NOT EXISTS dim_propiedad (
    id_propiedad_sk        BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_propiedad_natural   INT UNIQUE NOT NULL,
    tipo_operacion_actual  ENUM('Venta','Arriendo'),
    estado_actual          ENUM('Disponible','Vendida','Arrendada','En negociación'),
    ultima_transaccion_id  INT,
    fecha_ultimo_corte     DATE,
    fecha_carga            DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- --- DIM_CLIENTE ---
CREATE TABLE IF NOT EXISTS dim_cliente (
    id_cliente          INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id_natural  INT UNIQUE NOT NULL,
    nombre              VARCHAR(100) NOT NULL,
    apellido            VARCHAR(100) NOT NULL,
    email               VARCHAR(150),
    telefono            VARCHAR(30),
    tipo_cliente        ENUM('Comprador','Arrendatario','Inversionista') NOT NULL,
    presupuesto_max     DECIMAL(15,2),
    rango_presupuesto   ENUM('Bajo','Medio','Alto','Premium','Desconocido'),
    anio_registro       SMALLINT,
    fecha_registro      DATE
);

CREATE INDEX idx_cliente_tipo  ON dim_cliente(tipo_cliente);
CREATE INDEX idx_cliente_rango ON dim_cliente(rango_presupuesto);

-- --- DIM_AGENTE ---
CREATE TABLE IF NOT EXISTS dim_agente (
    id_agente              INT AUTO_INCREMENT PRIMARY KEY,
    agente_id_natural      INT UNIQUE NOT NULL,
    nombre                 VARCHAR(100) NOT NULL,
    apellido               VARCHAR(100) NOT NULL,
    email                  VARCHAR(150),
    telefono               VARCHAR(30),
    comision_pct           DECIMAL(5,2),
    comision_arriendo_pct  DECIMAL(5,2),
    fecha_ingreso          DATE,
    anio_ingreso           SMALLINT,
    antiguedad_anios       SMALLINT,
    rango_antiguedad       VARCHAR(20)
);

-- --- DIM_ESTADO_TRANSACCION ---
CREATE TABLE IF NOT EXISTS dim_estado_transaccion (
    id_estado_transaccion INT AUTO_INCREMENT PRIMARY KEY,
    nombre_estado         VARCHAR(30) UNIQUE NOT NULL,
    es_exitosa            BOOLEAN NOT NULL,
    descripcion           VARCHAR(120)
);

-- --- DIM_ESTADO_PROPIEDAD ---
CREATE TABLE IF NOT EXISTS dim_estado_propiedad (
    id_estado_propiedad INT AUTO_INCREMENT PRIMARY KEY,
    nombre_estado       VARCHAR(30) UNIQUE NOT NULL,
    es_disponible       BOOLEAN NOT NULL
);

-- --- FACT_TRANSACCIONES ---
CREATE TABLE IF NOT EXISTS fact_transacciones (
    transaccion_id      INT PRIMARY KEY,
    id_propiedad_sk     BIGINT NOT NULL,
    id_cliente          INT NOT NULL,
    id_agente           INT NOT NULL,
    id_tipo_operacion   INT NOT NULL,
    id_estado_trans     INT NOT NULL,
    id_fecha            INT NOT NULL,
    precio_lista        DECIMAL(15,2),
    precio_final        DECIMAL(15,2),
    descuento           DECIMAL(15,2),
    comision_valor      DECIMAL(15,2),
    FOREIGN KEY (id_propiedad_sk)   REFERENCES dim_propiedad(id_propiedad_sk),
    FOREIGN KEY (id_cliente)        REFERENCES dim_cliente(id_cliente),
    FOREIGN KEY (id_agente)         REFERENCES dim_agente(id_agente),
    FOREIGN KEY (id_tipo_operacion) REFERENCES dim_tipo_operacion(id_tipo_operacion),
    FOREIGN KEY (id_estado_trans)   REFERENCES dim_estado_transaccion(id_estado_transaccion),
    FOREIGN KEY (id_fecha)          REFERENCES dim_fecha(id_fecha)
);

CREATE INDEX idx_ftr_fecha   ON fact_transacciones(id_fecha);
CREATE INDEX idx_ftr_agente  ON fact_transacciones(id_agente);
CREATE INDEX idx_ftr_cliente ON fact_transacciones(id_cliente);
CREATE INDEX idx_ftr_estado  ON fact_transacciones(id_estado_trans);

-- --- FACT_ESTADO_PROPIEDAD_SNAPSHOT ---
CREATE TABLE IF NOT EXISTS fact_estado_propiedad_snapshot (
    id_snapshot           BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_propiedad_sk       BIGINT NOT NULL,
    id_fecha              INT NOT NULL,
    id_estado_propiedad   INT NOT NULL,
    ultima_transaccion_id INT,
    FOREIGN KEY (id_propiedad_sk)     REFERENCES dim_propiedad(id_propiedad_sk),
    FOREIGN KEY (id_fecha)            REFERENCES dim_fecha(id_fecha),
    FOREIGN KEY (id_estado_propiedad) REFERENCES dim_estado_propiedad(id_estado_propiedad),
    UNIQUE KEY uk_snap (id_propiedad_sk, id_fecha)
);

SELECT '✅ 04_gold_transaccional.sql ejecutado' AS resultado;
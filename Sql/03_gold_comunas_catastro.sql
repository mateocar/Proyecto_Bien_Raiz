USE inmobiliaria_gold;

ALTER TABLE dim_comuna
    ADD COLUMN avaluo_lotes_total DECIMAL(20,2) DEFAULT NULL
        COMMENT 'Avalúo catastral total de predios tipo Lote',
    ADD COLUMN fecha_carga_catastro DATETIME DEFAULT NULL
        COMMENT 'Última vez que se refrescó el dato catastral';

CREATE INDEX idx_comuna_avaluo_lotes ON dim_comuna(avaluo_lotes_total);

SELECT '✅ 03_gold_comunas_catastro.sql ejecutado' AS resultado;
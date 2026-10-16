USE inmobiliaria_gold;

-- 1. Conteo por tabla
SELECT 'dim_propiedad'    AS tabla, COUNT(*) AS filas FROM dim_propiedad
UNION ALL SELECT 'dim_cliente',         COUNT(*) FROM dim_cliente
UNION ALL SELECT 'dim_agente',          COUNT(*) FROM dim_agente
UNION ALL SELECT 'dim_comuna',          COUNT(*) FROM dim_comuna
UNION ALL SELECT 'dim_fecha',           COUNT(*) FROM dim_fecha
UNION ALL SELECT 'fact_propiedades',    COUNT(*) FROM fact_propiedades
UNION ALL SELECT 'fact_transacciones',  COUNT(*) FROM fact_transacciones;

-- 2. FKs huérfanas (deben ser 0)
SELECT 'FKs huérfanas en fact_propiedades' AS chequeo, COUNT(*) AS n
FROM fact_propiedades f
LEFT JOIN dim_tipo_propiedad t ON f.id_tipo_propiedad = t.id_tipo_propiedad
WHERE t.id_tipo_propiedad IS NULL
UNION ALL
SELECT 'FKs huérfanas en fact_transacciones', COUNT(*)
FROM fact_transacciones t
LEFT JOIN dim_propiedad p ON t.id_propiedad_sk = p.id_propiedad_sk
WHERE p.id_propiedad_sk IS NULL;

-- 3. Estados de propiedades
SELECT estado_actual, tipo_operacion_actual, COUNT(*) AS total
FROM dim_propiedad
GROUP BY estado_actual, tipo_operacion_actual
ORDER BY total DESC;

-- 4. Top 5 agentes por comisión
SELECT
    CONCAT(a.nombre, ' ', a.apellido) AS agente,
    COUNT(t.transaccion_id) AS num_ops,
    ROUND(SUM(t.comision_valor), 0) AS comision_total
FROM fact_transacciones t
JOIN dim_agente a ON t.id_agente = a.id_agente
JOIN dim_estado_transaccion et ON t.id_estado_trans = et.id_estado_transaccion
WHERE et.es_exitosa = TRUE
GROUP BY a.id_agente
ORDER BY comision_total DESC
LIMIT 5;
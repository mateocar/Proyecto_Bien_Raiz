import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from etl.config import get_connection, log


def query(sql: str) -> pd.DataFrame:
    """Ejecuta una consulta y devuelve un DataFrame."""
    conn = get_connection()
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


# ============================================================
# 1. VENTAS vs ARRIENDOS
# ============================================================
def ventas_vs_arriendos():
    sql = """
        SELECT
            op.nombre_operacion        AS operacion,
            COUNT(*)                   AS num_propiedades,
            ROUND(AVG(f.precio), 0)    AS precio_promedio,
            ROUND(MIN(f.precio), 0)    AS precio_min,
            ROUND(MAX(f.precio), 0)    AS precio_max,
            ROUND(AVG(f.area_construida), 1) AS area_promedio_m2
        FROM fact_propiedades f
        JOIN dim_tipo_operacion op ON f.id_tipo_operacion = op.id_tipo_operacion
        GROUP BY op.nombre_operacion
        ORDER BY num_propiedades DESC
    """
    return query(sql)


# ============================================================
# 2. TOP 10 BARRIOS POR PRECIO/M2
# ============================================================
def top_barrios():
    sql = """
        SELECT
            c.nombre_comuna      AS comuna,
            c.tipo_zona          AS tipo,
            COUNT(*)             AS num_propiedades,
            ROUND(AVG(f.precio), 0)         AS precio_promedio,
            ROUND(AVG(f.precio_por_m2), 0)  AS precio_m2
        FROM fact_propiedades f
        JOIN dim_ubicacion u ON f.id_ubicacion = u.id_ubicacion
        JOIN dim_comuna c    ON u.id_comuna = c.id_comuna
        WHERE f.precio_por_m2 IS NOT NULL
        GROUP BY c.nombre_comuna, c.tipo_zona
        HAVING num_propiedades >= 3
        ORDER BY precio_m2 DESC
        LIMIT 10
    """
    return query(sql)


# ============================================================
# 3. RENDIMIENTO DE AGENTES
# ============================================================
def rendimiento_agentes():
    sql = """
        SELECT
            CONCAT(a.nombre, ' ', a.apellido) AS agente,
            a.rango_antiguedad,
            COUNT(t.transaccion_id) AS total_ops,
            SUM(CASE WHEN et.es_exitosa THEN 1 ELSE 0 END) AS cerradas,
            SUM(CASE WHEN et.nombre_estado = 'Cancelada' THEN 1 ELSE 0 END) AS canceladas,
            ROUND(SUM(CASE WHEN et.es_exitosa THEN t.comision_valor ELSE 0 END), 0) AS comision_total,
            ROUND(100.0 * SUM(CASE WHEN et.es_exitosa THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(*), 0), 1) AS tasa_exito_pct
        FROM fact_transacciones t
        JOIN dim_agente a             ON t.id_agente = a.id_agente
        JOIN dim_estado_transaccion et ON t.id_estado_trans = et.id_estado_transaccion
        GROUP BY a.id_agente, agente, a.rango_antiguedad
        ORDER BY comision_total DESC
    """
    return query(sql)


# ============================================================
# 4. PROPIEDADES MÁS DEMANDADAS (configuración)
# ============================================================
def propiedades_demandadas():
    sql = """
        SELECT
            cf.habitaciones,
            cf.banos,
            cf.rango_tamano,
            COUNT(*)                 AS apariciones,
            ROUND(AVG(f.precio), 0)  AS precio_promedio
        FROM fact_propiedades f
        JOIN dim_caracteristica_fisica cf ON f.id_caracteristica = cf.id_caracteristica
        JOIN dim_tipo_operacion op        ON f.id_tipo_operacion = op.id_tipo_operacion
        WHERE op.es_venta = TRUE
        GROUP BY cf.habitaciones, cf.banos, cf.rango_tamano
        HAVING apariciones >= 2
        ORDER BY apariciones DESC
        LIMIT 10
    """
    return query(sql)


# ============================================================
# 5. EVOLUCIÓN MENSUAL DE TRANSACCIONES
# ============================================================
def evolucion_transacciones():
    sql = """
        SELECT
            df.anio_mes,
            COUNT(t.transaccion_id) AS total_transacciones,
            SUM(CASE WHEN et.es_exitosa THEN 1 ELSE 0 END) AS cerradas,
            ROUND(SUM(CASE WHEN et.es_exitosa THEN t.precio_final ELSE 0 END), 0) AS ingresos_cerrados
        FROM fact_transacciones t
        JOIN dim_fecha df              ON t.id_fecha = df.id_fecha
        JOIN dim_estado_transaccion et ON t.id_estado_trans = et.id_estado_transaccion
        GROUP BY df.anio_mes
        ORDER BY df.anio_mes
    """
    return query(sql)


# ============================================================
# 6. ESTADO DE PROPIEDADES (inventario actual)
# ============================================================
def estado_inventario():
    sql = """
        SELECT
            estado_actual,
            tipo_operacion_actual,
            COUNT(*) AS propiedades
        FROM dim_propiedad
        GROUP BY estado_actual, tipo_operacion_actual
        ORDER BY propiedades DESC
    """
    return query(sql)


# ============================================================
# MAIN
# ============================================================
def main():
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.float_format", lambda x: f"{x:,.0f}")

    log("=" * 70, "INFO")
    log("📊 1. Ventas vs Arriendos", "INFO")
    log("=" * 70, "INFO")
    print(ventas_vs_arriendos(), "\n")

    log("=" * 70, "INFO")
    log("🏆 2. Top 10 comunas por precio/m²", "INFO")
    log("=" * 70, "INFO")
    print(top_barrios(), "\n")

    log("=" * 70, "INFO")
    log("🧑‍💼 3. Rendimiento de agentes", "INFO")
    log("=" * 70, "INFO")
    print(rendimiento_agentes(), "\n")

    log("=" * 70, "INFO")
    log("🔥 4. Configuraciones más demandadas", "INFO")
    log("=" * 70, "INFO")
    print(propiedades_demandadas(), "\n")

    log("=" * 70, "INFO")
    log("📈 5. Evolución mensual de transacciones", "INFO")
    log("=" * 70, "INFO")
    print(evolucion_transacciones(), "\n")

    log("=" * 70, "INFO")
    log("🏘️  6. Estado del inventario", "INFO")
    log("=" * 70, "INFO")
    print(estado_inventario(), "\n")


if __name__ == "__main__":
    main()
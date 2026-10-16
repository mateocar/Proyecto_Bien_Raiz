import sys
from pathlib import Path
import pandas as pd
from mysql.connector import Error

sys.path.append(str(Path(__file__).resolve().parent.parent))

from etl.config import get_connection, PARQUET_SILVER, log


def cargar_caches(cursor):
    log("🔍 Construyendo cachés de dimensiones...", "INFO")
    cache = {}

    cursor.execute("""
        SELECT c.nombre_ciudad, co.nombre_comuna, u.id_ubicacion
        FROM dim_ubicacion u
        JOIN dim_comuna co ON u.id_comuna = co.id_comuna
        JOIN dim_ciudad c  ON co.id_ciudad = c.id_ciudad
    """)
    cache["ubicacion"] = {(r[0], r[1]): r[2] for r in cursor.fetchall()}

    cursor.execute("SELECT nivel_estrato, id_estrato FROM dim_estrato")
    cache["estrato"] = dict(cursor.fetchall())

    cursor.execute("SELECT nombre_tipo, id_tipo_propiedad FROM dim_tipo_propiedad")
    cache["tipo_prop"] = dict(cursor.fetchall())

    cursor.execute("SELECT nombre_operacion, id_tipo_operacion FROM dim_tipo_operacion")
    cache["tipo_op"] = dict(cursor.fetchall())

    cursor.execute("SELECT anio, id_tiempo FROM dim_tiempo_construccion")
    cache["tiempo"] = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute("""
        SELECT habitaciones, banos, rango_tamano, id_caracteristica
        FROM dim_caracteristica_fisica
    """)
    cache["caract"] = {(r[0], r[1], r[2]): r[3] for r in cursor.fetchall()}

    log(f"   ✅ ubicaciones={len(cache['ubicacion'])}, estratos={len(cache['estrato'])}, "
        f"tipos={len(cache['tipo_prop'])}, operaciones={len(cache['tipo_op'])}, "
        f"tiempos={len(cache['tiempo'])}, caracts={len(cache['caract'])}", "OK")
    return cache


def main():
    df = pd.read_parquet(PARQUET_SILVER)
    log(f"📥 Filas a procesar: {len(df)}", "INFO")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cache = cargar_caches(cursor)
        filas_insert = []
        errores = 0

        for _, row in df.iterrows():
            key_ubi = (row["ciudad"], row["barrio"])
            id_ubi = cache["ubicacion"].get(key_ubi)
            if not id_ubi:
                errores += 1
                continue

            estrato_key = int(row["estrato"]) if pd.notna(row["estrato"]) else -1
            id_estrato = cache["estrato"].get(estrato_key) or cache["estrato"].get(-1)
            if not id_estrato:
                errores += 1
                continue

            id_tipo = cache["tipo_prop"].get(row["tipo_propiedad"])
            id_op   = cache["tipo_op"].get(row["tipo_operacion"])
            if not id_tipo or not id_op:
                errores += 1
                continue

            anio_key = int(row["anio_construccion"]) if pd.notna(row["anio_construccion"]) else None
            id_tiempo = cache["tiempo"].get(anio_key) or cache["tiempo"].get(None)
            if not id_tiempo:
                errores += 1
                continue

            hab = int(row["habitaciones"]) if pd.notna(row["habitaciones"]) else None
            ban = float(row["banos"]) if pd.notna(row["banos"]) else None
            id_car = cache["caract"].get((hab, ban, row["rango_tamano"]))
            if not id_car:
                errores += 1
                continue

            filas_insert.append((
                id_ubi, id_estrato, id_tipo, id_op, id_tiempo, id_car,
                float(row["precio"]),
                float(row["area_construida"]) if pd.notna(row["area_construida"]) else None,
                float(row["area_total"]) if pd.notna(row["area_total"]) else None,
                float(row["precio_por_m2"]) if pd.notna(row["precio_por_m2"]) else None,
                row.get("enlace")
            ))

        sql = """
            INSERT INTO fact_propiedades
                (id_ubicacion, id_estrato, id_tipo_propiedad, id_tipo_operacion,
                 id_tiempo, id_caracteristica, precio, area_construida, area_total,
                 precio_por_m2, enlace_origen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(sql, filas_insert)
        conn.commit()

        log(f"✅ Insertadas {len(filas_insert)} filas en fact_propiedades", "OK")
        if errores:
            log(f"⚠️  Filas con error: {errores}", "WARN")

    except Error as e:
        log(f"❌ Error: {e}", "ERROR")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
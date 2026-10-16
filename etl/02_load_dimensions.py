import sys
from pathlib import Path
import pandas as pd
from mysql.connector import Error

sys.path.append(str(Path(__file__).resolve().parent.parent))

from etl.config import get_connection, PARQUET_SILVER, log


def get_or_create(cursor, tabla, col_id, col_busqueda, valor, extras=None):
    if pd.isna(valor):
        valor = "Desconocido"
    cursor.execute(f"SELECT {col_id} FROM {tabla} WHERE {col_busqueda} = %s", (valor,))
    r = cursor.fetchone()
    if r:
        return r[0]
    if extras:
        cols = [col_busqueda] + list(extras.keys())
        vals = [valor] + list(extras.values())
        ph = ", ".join(["%s"] * len(cols))
        cursor.execute(f"INSERT INTO {tabla} ({', '.join(cols)}) VALUES ({ph})", vals)
    else:
        cursor.execute(f"INSERT INTO {tabla} ({col_busqueda}) VALUES (%s)", (valor,))
    return cursor.lastrowid


def cargar_estratos(cursor, df):
    log("🏘️  Cargando estratos...", "INFO")
    cache = {}
    for nivel, clasif in df[["estrato", "clasificacion_estrato"]].drop_duplicates().values:
        nivel_int = int(nivel) if pd.notna(nivel) else -1
        cursor.execute("SELECT id_estrato FROM dim_estrato WHERE nivel_estrato = %s", (nivel_int,))
        r = cursor.fetchone()
        if r:
            cache[nivel_int] = r[0]
            continue
        cursor.execute(
            "INSERT INTO dim_estrato (nivel_estrato, clasificacion) VALUES (%s, %s)",
            (nivel_int, clasif)
        )
        cache[nivel_int] = cursor.lastrowid
    log(f"   ✅ {len(cache)} estratos", "OK")


def cargar_tipos_propiedad(cursor, df):
    log("🏠 Cargando tipos de propiedad...", "INFO")
    combos = df[["categoria_propiedad", "tipo_propiedad"]].drop_duplicates()
    for cat, tipo in combos.values:
        id_cat = get_or_create(cursor, "dim_categoria_propiedad",
                               "id_categoria", "nombre_categoria", cat)
        get_or_create(cursor, "dim_tipo_propiedad",
                      "id_tipo_propiedad", "nombre_tipo", tipo,
                      {"id_categoria": id_cat})
    log(f"   ✅ {len(combos)} tipos", "OK")


def cargar_tipos_operacion(cursor, df):
    log("🔑 Cargando tipos de operación...", "INFO")
    for op in df["tipo_operacion"].dropna().unique():
        es_venta = (str(op).lower() == "venta")
        cursor.execute("SELECT id_tipo_operacion FROM dim_tipo_operacion WHERE nombre_operacion = %s", (op,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO dim_tipo_operacion (nombre_operacion, es_venta) VALUES (%s, %s)",
                (op, es_venta)
            )
    log(f"   ✅ Operaciones cargadas", "OK")


def cargar_tiempo(cursor, df):
    log("📅 Cargando dimensión tiempo...", "INFO")
    combos = df[["anio_construccion", "decada", "rango_antiguedad"]].drop_duplicates()
    for anio, dec, rango in combos.values:
        anio_val = int(anio) if pd.notna(anio) else None
        es_desc = pd.isna(anio)
        cursor.execute(
            "SELECT id_tiempo FROM dim_tiempo_construccion WHERE "
            "(anio = %s OR (anio IS NULL AND %s IS NULL))",
            (anio_val, anio_val)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO dim_tiempo_construccion "
                "(anio, decada, rango_antiguedad, es_desconocido) VALUES (%s, %s, %s, %s)",
                (anio_val, dec, rango, bool(es_desc))
            )
    log(f"   ✅ {len(combos)} combinaciones", "OK")


def cargar_caracteristicas(cursor, df):
    log("📐 Cargando características físicas...", "INFO")
    combos = df[["habitaciones", "banos", "rango_tamano"]].drop_duplicates()
    for hab, ban, rango in combos.values:
        hab_val = int(hab) if pd.notna(hab) else None
        ban_val = float(ban) if pd.notna(ban) else None
        cursor.execute(
            "SELECT id_caracteristica FROM dim_caracteristica_fisica WHERE "
            "(habitaciones <=> %s) AND (banos <=> %s) AND (rango_tamano <=> %s)",
            (hab_val, ban_val, rango)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO dim_caracteristica_fisica (habitaciones, banos, rango_tamano) "
                "VALUES (%s, %s, %s)",
                (hab_val, ban_val, rango)
            )
    log(f"   ✅ {len(combos)} combinaciones", "OK")


def main():
    log("📥 Leyendo silver limpio...", "INFO")
    df = pd.read_parquet(PARQUET_SILVER)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cargar_estratos(cursor, df);           conn.commit()
        cargar_tipos_propiedad(cursor, df);    conn.commit()
        cargar_tipos_operacion(cursor, df);    conn.commit()
        cargar_tiempo(cursor, df);             conn.commit()
        cargar_caracteristicas(cursor, df);    conn.commit()
        log("\n✅ DIMENSIONES CARGADAS OK.", "OK")
    except Error as e:
        log(f"❌ Error: {e}", "ERROR")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
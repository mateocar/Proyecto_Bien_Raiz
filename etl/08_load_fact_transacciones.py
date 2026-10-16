import sys
from pathlib import Path
import pandas as pd
from mysql.connector import Error

sys.path.append(str(Path(__file__).resolve().parent.parent))

from etl.config import get_connection, DATA_DIR, log

ruta_sintetica = DATA_DIR / "base_de_datos_sintetica.xlsx"


def build_cache(cursor):
    log("🔍 Construyendo cachés...", "INFO")
    cache = {}
    for k, sql in [
        ("propiedad", "SELECT id_propiedad_natural, id_propiedad_sk FROM dim_propiedad"),
        ("cliente",   "SELECT cliente_id_natural, id_cliente FROM dim_cliente"),
        ("agente",    "SELECT agente_id_natural, id_agente FROM dim_agente"),
        ("tipo_op",   "SELECT nombre_operacion, id_tipo_operacion FROM dim_tipo_operacion"),
        ("estado",    "SELECT nombre_estado, id_estado_transaccion FROM dim_estado_transaccion"),
        ("fecha",     "SELECT id_fecha, id_fecha FROM dim_fecha"),
    ]:
        cursor.execute(sql)
        cache[k] = dict(cursor.fetchall())
    log(f"   ✅ {[(k, len(v)) for k, v in cache.items()]}", "OK")
    return cache


def main():
    log("📥 Leyendo transacciones...", "INFO")
    df = pd.read_excel(ruta_sintetica, "Transacciones")
    log(f"   Filas: {len(df)}", "INFO")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cache = build_cache(cursor)
        insertados = 0
        omitidos = 0

        for _, r in df.iterrows():
            prop_nat = int(r["propiedad_id"])
            id_prop = cache["propiedad"].get(prop_nat)
            id_cli  = cache["cliente"].get(int(r["cliente_id"]))
            id_age  = cache["agente"].get(int(r["agente_id"]))
            id_op   = cache["tipo_op"].get(r["tipo_transaccion"])
            id_est  = cache["estado"].get(r["estado"])

            fecha = pd.to_datetime(r["fecha_transaccion"]).date()
            id_fecha = int(fecha.strftime("%Y%m%d"))

            if not all([id_prop, id_cli, id_age, id_op, id_est]):
                omitidos += 1
                continue
            if id_fecha not in cache["fecha"]:
                omitidos += 1
                continue

            precio_lista = float(r["precio_lista"]) if pd.notna(r["precio_lista"]) else None
            precio_final = float(r["precio_final"]) if pd.notna(r["precio_final"]) else None
            descuento = (precio_lista - precio_final) if (precio_lista and precio_final) else None

            cursor.execute("""
                INSERT INTO fact_transacciones
                    (transaccion_id, id_propiedad_sk, id_cliente, id_agente,
                     id_tipo_operacion, id_estado_trans, id_fecha,
                     precio_lista, precio_final, descuento, comision_valor)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    precio_final   = VALUES(precio_final),
                    precio_lista   = VALUES(precio_lista),
                    descuento      = VALUES(descuento),
                    comision_valor = VALUES(comision_valor),
                    id_estado_trans = VALUES(id_estado_trans)
            """, (
                int(r["transaccion_id"]),
                id_prop, id_cli, id_age, id_op, id_est, id_fecha,
                precio_lista, precio_final, descuento,
                float(r["comision_valor"]) if pd.notna(r["comision_valor"]) else 0,
            ))
            insertados += 1

        conn.commit()
        log(f"✅ {insertados} transacciones cargadas | {omitidos} omitidas", "OK")
    except Error as e:
        log(f"❌ {e}", "ERROR")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
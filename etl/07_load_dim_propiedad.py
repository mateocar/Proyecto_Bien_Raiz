import sys
from pathlib import Path
import pandas as pd
from mysql.connector import Error

sys.path.append(str(Path(__file__).resolve().parent.parent))

from etl.config import get_connection, DATA_DIR, log

ruta_sintetica = DATA_DIR / "base_de_datos_sintetica.xlsx"


def main():
    log("📥 Leyendo Estado_Propiedades...", "INFO")
    df_est = pd.read_excel(ruta_sintetica, "Estado_Propiedades")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT id_fact FROM fact_propiedades")
        ids_oferta = {r[0] for r in cursor.fetchall()}

        log(f"   IDs en fact_propiedades: {len(ids_oferta)}", "INFO")
        log(f"   IDs en Estado_Propiedades: {len(df_est)}", "INFO")

        insertados = 0
        for _, r in df_est.iterrows():
            pid = int(r["propiedad_id"])
            cursor.execute("""
                INSERT INTO dim_propiedad
                    (id_propiedad_natural, tipo_operacion_actual, estado_actual,
                     ultima_transaccion_id, fecha_ultimo_corte)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    tipo_operacion_actual = VALUES(tipo_operacion_actual),
                    estado_actual = VALUES(estado_actual),
                    ultima_transaccion_id = VALUES(ultima_transaccion_id),
                    fecha_ultimo_corte = VALUES(fecha_ultimo_corte)
            """, (
                pid, r["tipo_operacion"], r["estado_propiedad"],
                int(r["ultima_transaccion_id"]) if pd.notna(r["ultima_transaccion_id"]) else None,
                pd.to_datetime(r["fecha_corte"]).date()
            ))
            insertados += 1

        # Asegurar que propiedades de la oferta también existan
        for pid in ids_oferta - set(df_est["propiedad_id"].astype(int)):
            cursor.execute("""
                INSERT IGNORE INTO dim_propiedad
                    (id_propiedad_natural, estado_actual)
                VALUES (%s, 'Disponible')
            """, (pid,))

        conn.commit()
        log(f"✅ dim_propiedad: {insertados} filas procesadas", "OK")

    except Error as e:
        log(f"❌ {e}", "ERROR")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
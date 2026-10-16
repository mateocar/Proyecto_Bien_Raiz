import sys
from pathlib import Path
import pandas as pd
from mysql.connector import Error

sys.path.append(str(Path(__file__).resolve().parent.parent))

from etl.config import get_connection, DATA_DIR, log

RUTA_CATASTRO = DATA_DIR / "informacion_catastral_por_uso.csv"


def limpiar_columnas(df):
    """Limpia BOM (\ufeff) y BOM latin-1 mal decodificado (ï»¿)."""
    df.columns = [
        c.strip()
         .lstrip("\ufeff").replace("\ufeff", "")
         .lstrip("ï»¿").replace("ï»¿", "")
        for c in df.columns
    ]
    return df


def main():
    log("📥 Leyendo catastro...", "INFO")
    df = pd.read_csv(RUTA_CATASTRO, encoding="latin-1")
    df = limpiar_columnas(df)

    log(f"   Columnas detectadas: {df.columns.tolist()}", "INFO")
    log(f"   Filas totales: {len(df)}", "INFO")

    df_lotes = df[df["nombre_uso"].str.strip().str.lower() == "lotes"].copy()
    log(f"   Filas 'Lotes': {len(df_lotes)}", "INFO")

    df_lotes = df_lotes[["codComuna", "nombre_comuna_oficial", "avaluo_total"]].copy()
    df_lotes["avaluo_total"] = pd.to_numeric(df_lotes["avaluo_total"], errors="coerce")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT cod_comuna, id_comuna FROM dim_comuna WHERE cod_comuna > 0")
        mapa = {r[0]: r[1] for r in cursor.fetchall()}
        log(f"\n   Comunas en dim_comuna: {len(mapa)}", "INFO")

        actualizadas = 0
        sin_match = []
        for _, row in df_lotes.iterrows():
            cod = int(row["codComuna"])
            id_com = mapa.get(cod)
            if not id_com:
                sin_match.append(row["nombre_comuna_oficial"])
                continue

            cursor.execute("""
                UPDATE dim_comuna
                SET avaluo_lotes_total   = %s,
                    fecha_carga_catastro = CURRENT_TIMESTAMP
                WHERE id_comuna = %s
            """, (
                float(row["avaluo_total"]) if pd.notna(row["avaluo_total"]) else None,
                id_com
            ))
            actualizadas += 1

        conn.commit()
        log(f"\n✅ {actualizadas} comunas enriquecidas con avalúo de Lotes", "OK")
        if sin_match:
            log(f"⚠️  Sin match: {sin_match}", "WARN")

        cursor.execute("""
            SELECT cod_comuna, nombre_comuna, tipo_zona, avaluo_lotes_total
            FROM dim_comuna
            WHERE avaluo_lotes_total IS NOT NULL
            ORDER BY avaluo_lotes_total DESC
            LIMIT 5
        """)
        log("\n📊 Top 5 comunas por avalúo de Lotes:", "INFO")
        for cod, nombre, tipo, avaluo in cursor.fetchall():
            log(f"   {nombre:<25} {tipo:<15} ${float(avaluo):>18,.0f}", "INFO")

    except Error as e:
        log(f"❌ Error: {e}", "ERROR")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
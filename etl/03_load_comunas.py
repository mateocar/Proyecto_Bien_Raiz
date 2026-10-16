import sys
from pathlib import Path
import pandas as pd
from mysql.connector import Error

sys.path.append(str(Path(__file__).resolve().parent.parent))

from etl.config import get_connection, DATA_DIR, PARQUET_SILVER, log

ruta_ubicaciones = DATA_DIR / "ubicaciones.csv"


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


def clasificar_zona(cod_comuna: int) -> str:
    return "Comuna" if cod_comuna <= 16 else "Corregimiento"


def main():
    log("📥 Leyendo maestros...", "INFO")
    df_ubi = pd.read_csv(ruta_ubicaciones, encoding="latin-1")
    df_silver = pd.read_parquet(PARQUET_SILVER)

    df_ubi.columns = [c.strip() for c in df_ubi.columns]
    df_ubi["zona_norm"] = df_ubi["zona"].str.strip().str.title()

    log(f"   Ubicaciones maestras: {len(df_ubi)}", "INFO")
    log(f"   Silver limpio:        {len(df_silver)}", "INFO")

    usadas = set(df_silver["barrio"].dropna().unique())
    maestras = set(df_ubi["zona_norm"].unique())
    log(f"\n🔎 Cobertura:", "INFO")
    log(f"   En silver no en maestro: {usadas - maestras}", "INFO")
    log(f"   En maestro no usadas:    {maestras - usadas}", "INFO")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        id_pais = get_or_create(cursor, "dim_pais", "id_pais", "nombre_pais", "Colombia")
        id_depto = get_or_create(cursor, "dim_departamento", "id_departamento",
                                 "nombre_departamento", "Antioquia",
                                 {"id_pais": id_pais})
        id_ciudad = get_or_create(cursor, "dim_ciudad", "id_ciudad",
                                  "nombre_ciudad", "Medellín",
                                  {"id_departamento": id_depto})

        log("\n🏘️  Cargando comunas desde el maestro...", "INFO")
        n = 0
        for _, row in df_ubi.iterrows():
            cursor.execute("""
                INSERT INTO dim_comuna
                    (cod_comuna, nombre_comuna, tipo_zona, latitud, longitud, id_ciudad)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    latitud   = VALUES(latitud),
                    longitud  = VALUES(longitud),
                    tipo_zona = VALUES(tipo_zona)
            """, (
                int(row["codComuna"]), row["zona_norm"],
                clasificar_zona(int(row["codComuna"])),
                float(row["latitud"]) if pd.notna(row["latitud"]) else None,
                float(row["longitud"]) if pd.notna(row["longitud"]) else None,
                id_ciudad
            ))
            n += 1
        log(f"   ✅ {n} comunas/corregimientos cargados", "OK")
        conn.commit()

        # Crear ubicaciones (hoja del fact)
        log("\n📍 Generando dim_ubicacion...", "INFO")
        cursor.execute("SELECT id_comuna, nombre_comuna FROM dim_comuna")
        mapa_comunas = {nombre: id_com for id_com, nombre in cursor.fetchall()}

        faltantes = usadas - set(mapa_comunas.keys())
        if faltantes:
            log(f"   ⚠️  Creando comuna 'Desconocido' para: {faltantes}", "WARN")
            id_desc = get_or_create(cursor, "dim_comuna", "id_comuna", "nombre_comuna",
                                    "Desconocido",
                                    {"cod_comuna": -1, "tipo_zona": "Desconocido",
                                     "id_ciudad": id_ciudad})
            for nombre in faltantes:
                mapa_comunas[nombre] = id_desc

        n_ubi = 0
        for nombre, id_com in mapa_comunas.items():
            cursor.execute("SELECT id_ubicacion FROM dim_ubicacion WHERE id_comuna = %s LIMIT 1",
                           (id_com,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO dim_ubicacion (id_comuna) VALUES (%s)", (id_com,))
                n_ubi += 1
        log(f"   ✅ {n_ubi} ubicaciones nuevas", "OK")
        conn.commit()
        log("\n🎉 Jerarquía geográfica lista.", "OK")
    except Error as e:
        log(f"❌ Error: {e}", "ERROR")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
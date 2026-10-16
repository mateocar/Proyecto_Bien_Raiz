import sys
from pathlib import Path
from datetime import date, timedelta
import pandas as pd
from mysql.connector import Error

sys.path.append(str(Path(__file__).resolve().parent.parent))

from etl.config import get_connection, DATA_DIR, log

ruta_sintetica = DATA_DIR / "base_de_datos_sintetica.xlsx"


def rango_presupuesto(p):
    if pd.isna(p):        return "Desconocido"
    if p < 300_000_000:   return "Bajo"
    if p < 800_000_000:   return "Medio"
    if p < 2_000_000_000: return "Alto"
    return "Premium"


def rango_antiguedad(a):
    if pd.isna(a):  return "Nuevo"
    if a <= 2:      return "Nuevo"
    if a <= 5:      return "Junior"
    if a <= 10:     return "Senior"
    return "Veterano"


def load_clientes(cursor, df):
    log("👥 Cargando dim_cliente...", "INFO")
    for _, r in df.iterrows():
        cursor.execute("""
            INSERT INTO dim_cliente
                (cliente_id_natural, nombre, apellido, email, telefono,
                 tipo_cliente, presupuesto_max, rango_presupuesto,
                 anio_registro, fecha_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                presupuesto_max = VALUES(presupuesto_max),
                rango_presupuesto = VALUES(rango_presupuesto),
                tipo_cliente = VALUES(tipo_cliente)
        """, (
            int(r["cliente_id"]), r["nombre"], r["apellido"],
            r["email"], r["telefono"], r["tipo_cliente"],
            float(r["presupuesto_max"]) if pd.notna(r["presupuesto_max"]) else None,
            rango_presupuesto(r["presupuesto_max"]),
            pd.to_datetime(r["fecha_registro"]).year if pd.notna(r["fecha_registro"]) else None,
            pd.to_datetime(r["fecha_registro"]).date() if pd.notna(r["fecha_registro"]) else None,
        ))
    log(f"   ✅ {len(df)} clientes", "OK")


def load_agentes(cursor, df):
    log("🧑‍💼 Cargando dim_agente...", "INFO")
    hoy = date.today()
    for _, r in df.iterrows():
        fi = pd.to_datetime(r["fecha_ingreso"]).date() if pd.notna(r["fecha_ingreso"]) else None
        antig = (hoy - fi).days // 365 if fi else None
        cursor.execute("""
            INSERT INTO dim_agente
                (agente_id_natural, nombre, apellido, email, telefono,
                 comision_pct, comision_arriendo_pct, fecha_ingreso,
                 anio_ingreso, antiguedad_anios, rango_antiguedad)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                comision_pct = VALUES(comision_pct),
                comision_arriendo_pct = VALUES(comision_arriendo_pct)
        """, (
            int(r["agente_id"]), r["nombre"], r["apellido"],
            r["email"], r["telefono"],
            float(r["comision_pct"]), float(r["comision_arriendo_pct"]),
            fi, fi.year if fi else None, antig, rango_antiguedad(antig)
        ))
    log(f"   ✅ {len(df)} agentes", "OK")


def load_estados(cursor, estados_trans, estados_prop):
    log("🏷️  Cargando estados...", "INFO")
    for e, exitosa in [("Cerrada", True), ("Cancelada", False), ("En Proceso", False)]:
        cursor.execute("""
            INSERT INTO dim_estado_transaccion (nombre_estado, es_exitosa, descripcion)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE es_exitosa = VALUES(es_exitosa)
        """, (e, exitosa, f"Estado '{e}'"))

    for e in estados_prop.unique():
        cursor.execute("""
            INSERT INTO dim_estado_propiedad (nombre_estado, es_disponible)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE es_disponible = VALUES(es_disponible)
        """, (e, e in ("Disponible", "En negociación")))
    log("   ✅ Estados cargados", "OK")


def load_dim_fecha(cursor, fecha_min, fecha_max):
    log(f"📅 Cargando dim_fecha ({fecha_min} → {fecha_max})...", "INFO")
    MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    DIAS = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

    d = fecha_min
    n = 0
    while d <= fecha_max:
        cursor.execute("""
            INSERT IGNORE INTO dim_fecha
                (id_fecha, fecha, anio, trimestre, mes, nombre_mes,
                 dia, dia_semana, nombre_dia, es_fin_semana, anio_mes, anio_trimestre)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            int(d.strftime("%Y%m%d")), d,
            d.year, (d.month - 1)//3 + 1, d.month, MESES[d.month-1],
            d.day, d.weekday(), DIAS[d.weekday()], d.weekday() >= 5,
            d.strftime("%Y-%m"), f"{d.year}-Q{(d.month-1)//3 + 1}"
        ))
        d += timedelta(days=1)
        n += 1
    log(f"   ✅ {n} fechas", "OK")


def main():
    log("📥 Leyendo Excel...", "INFO")
    xls = pd.ExcelFile(ruta_sintetica)
    df_cli = pd.read_excel(xls, "Clientes")
    df_age = pd.read_excel(xls, "Agentes")
    df_tra = pd.read_excel(xls, "Transacciones")
    df_est = pd.read_excel(xls, "Estado_Propiedades")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        load_clientes(cursor, df_cli); conn.commit()
        load_agentes(cursor, df_age);  conn.commit()
        load_estados(cursor, df_tra["estado"].unique(),
                     df_est["estado_propiedad"].unique())
        conn.commit()

        fmin = min(df_tra["fecha_transaccion"].min(), df_est["fecha_corte"].min())
        fmax = max(df_tra["fecha_transaccion"].max(), df_est["fecha_corte"].max())
        load_dim_fecha(cursor, fmin.date(), fmax.date())
        conn.commit()

        log("\n✅ Dimensiones de negocio cargadas.", "OK")
    except Error as e:
        log(f"❌ {e}", "ERROR")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
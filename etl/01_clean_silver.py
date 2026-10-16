import re
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from etl.config import DATA_DIR, PARQUET_SILVER, log


ruta_silver = DATA_DIR / "data_propiedades_medellin_final.csv"

def limpiar_precio(val):
    """'$ 550.000.000' -> 550000000.0"""
    if pd.isna(val):
        return np.nan
    s = re.sub(r"[^\d,.-]", "", str(val))
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan


def limpiar_area(val):
    """'104 m²' -> 104.0  |  '111,99 m²' -> 111.99"""
    if pd.isna(val):
        return np.nan
    s = re.sub(r"[^\d,.]", "", str(val))
    s = s.replace(",", ".")
    if s.count(".") > 1:
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return np.nan


def limpiar_habitaciones(val):
    """'4 habitaciones' -> 4  |  '3.0' -> 3"""
    if pd.isna(val):
        return np.nan
    m = re.search(r"(\d+(?:[.,]\d+)?)", str(val).lower())
    return int(float(m.group(1).replace(",", "."))) if m else np.nan


def limpiar_banos(val):
    """'2 baños' -> 2.0  |  '3,5 baños' -> 3.5"""
    if pd.isna(val):
        return np.nan
    m = re.search(r"(\d+(?:[.,]\d+)?)", str(val).lower())
    return float(m.group(1).replace(",", ".")) if m else np.nan


def normalizar_texto(val):
    """'buenos aires' -> 'Buenos Aires'"""
    if pd.isna(val):
        return None
    return str(val).strip().title()


def split_ubicacion(val):
    """'El Poblado, Medellín, Colombia' -> (barrio, ciudad, depto, pais)"""
    if pd.isna(val):
        return (None, None, None, None)
    partes = [p.strip() for p in str(val).split(",")]
    while len(partes) < 4:
        partes.append(None)
    return (
        normalizar_texto(partes[0]),
        normalizar_texto(partes[1]) or "Medellín",
        normalizar_texto(partes[2]) or "Antioquia",
        normalizar_texto(partes[3]) or "Colombia",
    )


def rango_tamano(area):
    if pd.isna(area):  return "Desconocido"
    if area < 50:      return "Pequeño"
    if area < 100:     return "Mediano"
    if area < 200:     return "Grande"
    return "Muy grande"


def rango_antiguedad(anio, anio_actual=2025):
    if pd.isna(anio):  return "Desconocido"
    edad = anio_actual - int(anio)
    if edad <= 5:      return "Nuevo"
    if edad <= 15:     return "Reciente"
    if edad <= 40:     return "Antiguo"
    return "Muy antiguo"


def clasificar_estrato(nivel):
    if pd.isna(nivel):  return "Desconocido"
    n = int(nivel)
    if n <= 2:  return "Bajo"
    if n <= 4:  return "Medio"
    return "Alto"


def categoria_propiedad(tipo):
    if pd.isna(tipo):  return "Otros"
    t = str(tipo).lower()
    if any(x in t for x in ["apartamento", "casa", "apartaestudio", "villa"]):
        return "Residencial"
    if any(x in t for x in ["oficina", "local", "bodega"]):
        return "Comercial"
    return "Otros"


# ---------- PIPELINE ----------

def main():
    log("📥 Leyendo Silver...", "INFO")
    df = pd.read_csv(ruta_silver, sep=";", dtype=str, encoding="latin-1")
    log(f"   Filas originales: {len(df)}", "INFO")

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Limpieza
    log("🧹 Limpiando...", "INFO")
    df["precio"]            = df["precio"].apply(limpiar_precio)
    df["area_construida"]   = df["area_construida"].apply(limpiar_area)
    df["area_total"]        = df["area_total"].apply(limpiar_area)
    df["habitaciones"]      = df["habitaciones"].apply(limpiar_habitaciones)
    df["banos"]             = df["banos"].apply(limpiar_banos)
    df["anio_construccion"] = pd.to_numeric(df["anio_construccion"], errors="coerce")
    df["estrato"]           = pd.to_numeric(df["estrato"], errors="coerce")
    df["tipo_propiedad"]    = df["tipo_propiedad"].apply(normalizar_texto)
    df["tipo_operacion"]    = df["tipo_operacion"].str.strip().str.title()

    # Split ubicación
    ubicaciones = df["ubicacion"].apply(split_ubicacion)
    df[["barrio", "ciudad", "departamento", "pais"]] = pd.DataFrame(
        ubicaciones.tolist(), index=df.index
    )

    # Derivados
    df["rango_tamano"]          = df["area_construida"].apply(rango_tamano)
    df["decada"]                = df["anio_construccion"].apply(
        lambda x: f"{int(x)//10*10}s" if pd.notna(x) else "Desconocido"
    )
    df["rango_antiguedad"]      = df["anio_construccion"].apply(rango_antiguedad)
    df["clasificacion_estrato"] = df["estrato"].apply(clasificar_estrato)
    df["categoria_propiedad"]   = df["tipo_propiedad"].apply(categoria_propiedad)

    df["precio_por_m2"] = np.where(
        (df["area_construida"] > 0) & df["precio"].notna(),
        df["precio"] / df["area_construida"],
        np.nan
    )

    # Descartar filas sin precio
    antes = len(df)
    df = df[df["precio"].notna() & (df["precio"] > 0)].copy()
    log(f"   Filas descartadas sin precio válido: {antes - len(df)}", "WARN")

    log(f"\n📊 Resumen:", "INFO")
    log(f"   Filas finales:    {len(df)}", "INFO")
    log(f"   Precio medio:     ${df['precio'].mean():,.0f}", "INFO")
    log(f"   Barrios únicos:   {df['barrio'].nunique()}", "INFO")
    log(f"   Tipos propiedad:  {df['tipo_propiedad'].nunique()}", "INFO")
    log(f"   Operaciones:      {df['tipo_operacion'].unique().tolist()}", "INFO")

    df.to_parquet(PARQUET_SILVER, index=False)
    log(f"✅ Guardado en: {PARQUET_SILVER}", "OK")


if __name__ == "__main__":
    main()
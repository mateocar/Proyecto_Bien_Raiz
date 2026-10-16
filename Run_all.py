import subprocess
import sys
from etl.config import log


PIPELINE = [
    "etl.01_clean_silver",
    "etl.02_load_dimensions",
    "etl.03_load_comunas",
    "etl.04_load_fact_propiedades",
    "etl.05_enrich_comuna_lotes",
    "etl.06_load_dims_negocio",
    "etl.07_load_dim_propiedad",
    "etl.08_load_fact_transacciones",
]

def run_step(module: str) ->bool: 
    log(f"▶️  Ejecutando {module}...", "INFO")
    r = subprocess.run([sys.executable, "-m", module])
    if r.returncode != 0:
        log(f"❌ Falló: {module}", "ERROR")
        return False
    log(f"✅ OK: {module}", "OK")

    return True


if __name__ == "main":
    log("🚀 Pipeline iniciado", "INFO")
    for m in PIPELINE:
        if not run_step(m):
            log("🛑 Abortado", "ERROR")
            sys.exit(1)
    log("🎉 Pipeline completo", "OK")
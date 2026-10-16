import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from etl.config import get_connection, DB_NAME, log

try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    cursor.execute(f"USE {DB_NAME}")
    cursor.execute("SHOW TABLES")
    tables = [r[0] for r in cursor.fetchall()]

    log(f"✅ Conectado a MySQL {version}", "OK")
    log(f"✅ Base de datos: {DB_NAME}", "OK")
    log(f"✅ Tablas encontradas: {len(tables)}", "OK")

    for t in tables:
        print(f"  - {t}")

    cursor.close()
    conn.close()
except Exception as e:
    log(f"❌ Error: {e}", "ERROR")
    sys.exit(1)

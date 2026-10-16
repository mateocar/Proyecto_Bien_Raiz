import os
import mysql.connector
from pathlib import Path
from dotenv import load_dotenv
from colorama import Fore, Style, init


load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "charset": "utf8mb4"
}

DB_NAME  = os.getenv("DB_NAME","inmobiliaria_gold")

DB_CONFIG_WITH_DB = {**DB_CONFIG, "database": DB_NAME}

ROOT       = Path(__file__).resolve().parent.parent
DATA_DIR   = ROOT / "Data"
SQL_DIR    = ROOT / "Sql"
LOGS_DIR   = ROOT / "Logs"
PARQUET_SILVER = DATA_DIR / "silver_limpio.parquet"


def get_connection(with_db: bool = True):
    """Devuelve una conexión a MySQL."""
    cfg = DB_CONFIG_WITH_DB if with_db else DB_CONFIG
    return mysql.connector.connect(**cfg)


def log(msg: str, nivel: str = "INFO"):
    """Log simple con color."""
    init(autoreset=True)
    colores = {
        "INFO":  Fore.CYAN,
        "OK":    Fore.GREEN,
        "WARN":  Fore.YELLOW,
        "ERROR": Fore.RED,
    }
    print(f"{colores.get(nivel, '')}[{nivel}]{Style.RESET_ALL} {msg}")

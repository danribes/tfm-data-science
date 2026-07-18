"""Centralized path and API constants for the housing affordability project."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
CHARTS_DIR = ROOT / "charts"

INE_BASE_URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA"

# INE table IDs
TABLES = {
    # Índice de Precios de Vivienda por CCAA — anual
    "ipv_ccaa_anual": 49300,
    # Índice de Precios de Vivienda por CCAA — trimestral
    "ipv_ccaa_trimestral": 76201,
    # IPC por CCAA — general e índices por grupos ECOICOP
    "ipc_ccaa": 76136,
    # Salario bruto anual: medias y percentiles por CCAA
    "salario_ccaa": 28191,
}

# Output file names
RAW_FILES = {
    "ipv_ccaa_anual": DATA_RAW / "ipv_ccaa_anual.json",
    "ipv_ccaa_trimestral": DATA_RAW / "ipv_ccaa_trimestral.json",
    "ipc_ccaa": DATA_RAW / "ipc_ccaa.json",
    "salario_ccaa": DATA_RAW / "salario_ccaa.json",
}

PROCESSED_FILES = {
    "ipv": DATA_PROCESSED / "ipv_ccaa.csv",
    "ipc": DATA_PROCESSED / "ipc_ccaa.csv",
    "salario": DATA_PROCESSED / "salario_ccaa.csv",
    "asequibilidad": DATA_PROCESSED / "asequibilidad_ccaa.csv",
}

CCAA_NAMES = {
    "Andalucía", "Aragón", "Asturias, Principado de", "Balears, Illes",
    "Canarias", "Cantabria", "Castilla y León", "Castilla - La Mancha",
    "Cataluña", "Comunitat Valenciana", "Extremadura", "Galicia",
    "Madrid, Comunidad de", "Murcia, Región de", "Navarra, Comunidad Foral de",
    "País Vasco", "Rioja, La",
}

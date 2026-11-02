"""Configuracion central: areas, bases de datos y parametros del modelo."""
import os
from datetime import date
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

RAIZ = Path(__file__).parent
if load_dotenv:
    load_dotenv(RAIZ / ".env", override=True)

DATOS = RAIZ / "datos"

# Clave de Groq (empieza con gsk_). Se limpian espacios y comillas por si quedaron al pegarla.
API_KEY = (os.getenv("GROQ_API_KEY") or "").strip().strip("\"'")

# Modelo. Se puede cambiar con GROQ_MODEL en el .env
MODELO = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Segundos de espera maximos por llamada
TIMEOUT_SEG = 60

# Maximo de filas que se leen por consulta
MAX_FILAS = 200

# Fecha hasta la que llegan los datos de ejemplo
FECHA_CORTE = date(2026, 10, 25)

AREAS = {
    "comercial": {
        "nombre": "Comercial",
        "db": DATOS / "comercial.db",
        "descripcion": "clientes, proyectos, unidades en venta, cotizaciones y ventas",
        "instrucciones": "Los precios de las unidades estan en UF.",
    },
    "finanzas": {
        "nombre": "Finanzas y Operaciones",
        "db": DATOS / "finanzas_operaciones.db",
        "descripcion": "proveedores, presupuestos, facturas, pagos y flujo de caja",
        "instrucciones": "Los montos estan en pesos chilenos (CLP).",
    },
    "tecnica": {
        "nombre": "Tecnica",
        "db": DATOS / "tecnica.db",
        "descripcion": "obras, etapas, contratistas, inspecciones y permisos",
        "instrucciones": "El avance se mide en porcentaje (0 a 100).",
    },
}
"""Comprueba, sin usar la API, que las bases existen y que son de solo lectura.

Uso:  python verificar.py
"""
import sqlite3

from asistente import Asistente, ConsultaNoPermitida
from config import AREAS

INTENTOS_PROHIBIDOS = [
    "DELETE FROM {t}",
    "UPDATE {t} SET id = 0",
    "DROP TABLE {t}",
    "INSERT INTO {t} (id) VALUES (999999)",
    "SELECT 1; DROP TABLE {t}",
    "ATTACH DATABASE ':memory:' AS x",
    "PRAGMA writable_schema = ON",
]

ok = True
for clave, area in AREAS.items():
    a = Asistente(clave)
    tabla = a.con.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]
    print(f"\n{area['nombre']} ({area['db'].name})")

    for (t,) in a.con.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'").fetchall():
        n = a.con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} filas")

    for plantilla in INTENTOS_PROHIBIDOS:
        sql = plantilla.format(t=tabla)
        try:
            a.ejecutar(sql)
            print(f"  FALLA, se ejecutó: {sql}")
            ok = False
        except (ConsultaNoPermitida, sqlite3.Error):
            pass
    print(f"  {len(INTENTOS_PROHIBIDOS)} intentos de escritura bloqueados")

print("\nTodo en orden." if ok else "\nHay fallas, revisa arriba.")

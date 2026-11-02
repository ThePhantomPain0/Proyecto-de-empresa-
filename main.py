"""Consulta por terminal a los asistentes de cada area.

Ejemplos:
    python main.py                          menu para elegir area
    python main.py comercial                chat con el asistente Comercial
    python main.py finanzas -p "Cuantas facturas vencidas hay?"
    python main.py tecnica --sql            muestra tambien el SQL generado
"""
import argparse
import os
import sys

from asistente import Asistente
from config import AREAS


def elegir_area():
    claves = list(AREAS)
    for i, clave in enumerate(claves, 1):
        print(f"{i}. {AREAS[clave]['nombre']}")
    while True:
        op = input("Área: ").strip().lower()
        if op.isdigit() and 1 <= int(op) <= len(claves):
            return claves[int(op) - 1]
        if op in AREAS:
            return op
        print("Opción no válida.")


def responder(asistente, pregunta, mostrar_sql):
    try:
        r = asistente.preguntar(pregunta)
    except Exception as e:  # error de red, clave inválida, etc.
        print(f"Error al consultar: {e}\n")
        return
    if mostrar_sql and r.sql:
        print(f"\n[SQL]\n{r.sql}")
    print(f"\n{r.respuesta}\n")


def main():
    parser = argparse.ArgumentParser(description="Asistentes de consulta por área")
    parser.add_argument("area", nargs="?", choices=list(AREAS), help="área a consultar")
    parser.add_argument("-p", "--pregunta", help="hace una sola pregunta y termina")
    parser.add_argument("--sql", action="store_true", help="muestra el SQL generado")
    args = parser.parse_args()

    if not os.getenv("GROQ_API_KEY"):
        sys.exit("Falta GROQ_API_KEY. Copia .env.example a .env y pega tu clave.")
    area = args.area or elegir_area()
    asistente = Asistente(area)

    if args.pregunta:
        responder(asistente, args.pregunta, args.sql)
        return

    print(f"\nAsistente {AREAS[area]['nombre']} (solo lectura). Escribe 'salir' para terminar.\n")
    while True:
        pregunta = input("Pregunta: ").strip()
        if pregunta.lower() in {"salir", "exit", "q"}:
            break
        if pregunta:
            responder(asistente, pregunta, args.sql)


if __name__ == "__main__":
    main()

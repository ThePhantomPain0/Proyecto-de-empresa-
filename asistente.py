"""Asistente de consulta por area: pregunta en lenguaje natural -> SQL -> respuesta.

Seguridad (solo lectura), en tres capas independientes:
  1. La base se abre en modo ro (read-only) de SQLite.
  2. Un autorizador de SQLite rechaza todo lo que no sea leer datos.
  3. Se exige que la consulta empiece con SELECT o WITH y sea una sola sentencia.
Aunque el modelo generara un DELETE, las capas 1 y 2 lo bloquean.
"""
import json
import re
import sqlite3
from dataclasses import dataclass

from config import API_KEY, AREAS, FECHA_CORTE, MAX_FILAS, MODELO, TIMEOUT_SEG
# Codigos de accion de SQLite que si se permiten: SELECT, READ, FUNCTION, RECURSIVE
_ACCIONES_PERMITIDAS = {21, 20, 31, 33}


def _autorizador(accion, *_):
    return 0 if accion in _ACCIONES_PERMITIDAS else 1  # 0 = OK, 1 = DENY


class ConsultaNoPermitida(Exception):
    pass


@dataclass
class Resultado:
    pregunta: str
    sql: str | None
    columnas: list
    filas: list
    respuesta: str


PROMPT_SQL = """Eres analista de datos del Consorcio Inmobiliario de la Ciudad, area {nombre}.
Datos disponibles: {descripcion}. {instrucciones}
Fecha de corte de los datos: {fecha_corte}. Usala como "hoy" en preguntas de plazos y vencimientos.

Tu unica tarea es escribir UNA consulta SQL de SQLite (solo SELECT) que responda la pregunta.
Reglas:
- Devuelve solo el SQL, sin explicaciones ni bloques de codigo.
- Usa solo las tablas y columnas del esquema.
- Si la pregunta no se puede responder con estas tablas, devuelve exactamente: NO_RESPONDIBLE

Esquema (los comentarios -- explican los valores posibles de cada columna):
{esquema}
"""

PROMPT_RESPUESTA = """Eres asistente del Gerente General del Consorcio Inmobiliario de la Ciudad, area {nombre}.
Respondes en español, directo y con cifras. Usa solo los datos del resultado, sin inventar nada.
Si el resultado esta vacio, dilo. Si hay montos, indica la unidad ({instrucciones}).
{aviso}"""


class Asistente:
    def __init__(self, clave_area):
        if clave_area not in AREAS:
            raise ValueError(f"Area desconocida: {clave_area}. Opciones: {', '.join(AREAS)}")
        self.area = AREAS[clave_area]
        ruta = self.area["db"]
        if not ruta.exists():
            raise FileNotFoundError(f"No existe {ruta}. Ejecuta primero: python crear_bases.py")

        self.con = sqlite3.connect(f"{ruta.resolve().as_uri()}?mode=ro", uri=True)
        self.esquema = self._leer_esquema()
        self.con.execute("PRAGMA query_only = ON")
        self.con.set_authorizer(_autorizador)  # desde aqui solo se puede leer
        self._cliente = None

    # ------------------------------------------------------------- base de datos
    def _leer_esquema(self):
        filas = self.con.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        return "\n".join(f[0] + ";" for f in filas)

    def ejecutar(self, sql):
        sql = sql.strip().rstrip(";").strip()
        if ";" in sql:
            raise ConsultaNoPermitida("Solo se permite una sentencia por consulta.")
        if not re.match(r"(?is)^(select|with)\b", sql):
            raise ConsultaNoPermitida("Solo se permiten consultas SELECT.")
        cur = self.con.execute(sql)
        filas = cur.fetchmany(MAX_FILAS)
        columnas = [d[0] for d in cur.description]
        return columnas, filas

    # ---------------------------------------------------------------------- IA
    @property
    def cliente(self):
        if self._cliente is None:
            from groq import Groq
            self._cliente = Groq(api_key=API_KEY, timeout=TIMEOUT_SEG)
        return self._cliente
    
    def _llamar(self, sistema, mensajes, temperatura=0.0):
        r = self.cliente.chat.completions.create(
            model=MODELO,
            messages=[{"role": "system", "content": sistema}] + mensajes,
            temperature=temperatura,
        )
        return (r.choices[0].message.content or "").strip()

    def _generar_sql(self, mensajes):
        sistema = PROMPT_SQL.format(
            nombre=self.area["nombre"], descripcion=self.area["descripcion"],
            instrucciones=self.area["instrucciones"], fecha_corte=FECHA_CORTE.isoformat(),
            esquema=self.esquema,
        )
        texto = self._llamar(sistema, mensajes, 0.0)
        return re.sub(r"^```(?:sql)?\s*|\s*```$", "", texto, flags=re.I).strip()

    def preguntar(self, pregunta):
        mensajes = [{"role": "user", "content": pregunta}]
        columnas = filas = sql = None

        for _ in range(2):  # un reintento si la consulta falla
            sql = self._generar_sql(mensajes)
            if sql.upper().startswith("NO_RESPONDIBLE"):
                texto = (f"Esa pregunta no se puede responder con la información del área "
                         f"{self.area['nombre']} ({self.area['descripcion']}).")
                return Resultado(pregunta, None, [], [], texto)
            try:
                columnas, filas = self.ejecutar(sql)
                break
            except (ConsultaNoPermitida, sqlite3.Error) as e:
                mensajes += [
                    {"role": "assistant", "content": sql},
                    {"role": "user", "content": f"Esa consulta falló: {e}. Corrígela y devuelve solo el SQL."},
                ]
        if filas is None:
            return Resultado(pregunta, sql, [], [], "No pude armar una consulta válida para esa pregunta. Prueba reformulándola.")

        aviso = (f"El resultado se cortó en {MAX_FILAS} filas; menciónalo."
                 if len(filas) >= MAX_FILAS else "")
        sistema = PROMPT_RESPUESTA.format(
            nombre=self.area["nombre"], instrucciones=self.area["instrucciones"], aviso=aviso
        )
        datos = json.dumps({"columnas": columnas, "filas": filas}, ensure_ascii=False, default=str)
        contenido = f"Pregunta: {pregunta}\n\nSQL ejecutado:\n{sql}\n\nResultado:\n{datos}"
        respuesta = self._llamar(sistema, [{"role": "user", "content": contenido}], 0.3)
        return Resultado(pregunta, sql, columnas, filas, respuesta)

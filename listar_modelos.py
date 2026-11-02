"""Lista los modelos de Gemini disponibles para tu clave.

Uso:  python listar_modelos.py
Copia el nombre (sin el prefijo models/) en GEMINI_MODEL dentro de .env
"""
from google import genai

import config 

cliente = genai.Client()
for m in cliente.models.list():
    acciones = getattr(m, "supported_actions", None) or []
    if "generateContent" in acciones:
        print(m.name.removeprefix("models/"))

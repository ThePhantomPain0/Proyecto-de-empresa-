"""Genera las tres bases de datos de ejemplo en la carpeta datos/.

Los datos son ficticios. Si ya existen los .db, este script los reemplaza.
Uso:  python crear_bases.py
"""
import random
import sqlite3
import unicodedata
from datetime import date, timedelta

from config import AREAS, DATOS, FECHA_CORTE

random.seed(42)
HOY = FECHA_CORTE

# Los mismos proyectos aparecen en las tres areas
PROYECTOS = [
    {"nombre": "Condominio Los Alerces", "comuna": "Valdivia", "tipo": "Casas",
     "lanzamiento": date(2024, 8, 1), "inicio_obra": date(2024, 11, 4),
     "termino": date(2026, 12, 15), "avance": 72, "unidades": 36, "vendido": 0.60},
    {"nombre": "Edificio Costanera 450", "comuna": "Valdivia", "tipo": "Departamentos",
     "lanzamiento": date(2025, 2, 10), "inicio_obra": date(2025, 5, 12),
     "termino": date(2027, 3, 30), "avance": 48, "unidades": 48, "vendido": 0.50},
    {"nombre": "Parque Calle-Calle", "comuna": "Valdivia", "tipo": "Casas",
     "lanzamiento": date(2025, 9, 1), "inicio_obra": date(2025, 11, 3),
     "termino": date(2027, 8, 20), "avance": 25, "unidades": 30, "vendido": 0.30},
    {"nombre": "Torre Pichi Ruca", "comuna": "Panguipulli", "tipo": "Departamentos",
     "lanzamiento": date(2026, 3, 1), "inicio_obra": date(2026, 6, 1),
     "termino": date(2028, 2, 28), "avance": 12, "unidades": 40, "vendido": 0.15},
    {"nombre": "Villa Los Notros", "comuna": "La Unión", "tipo": "Casas",
     "lanzamiento": date(2023, 6, 1), "inicio_obra": date(2023, 9, 4),
     "termino": date(2026, 6, 30), "avance": 100, "unidades": 24, "vendido": 0.95},
]

NOMBRES = ["Camila", "Matías", "Francisca", "Diego", "Valentina", "Sebastián", "Javiera",
           "Nicolás", "Constanza", "Felipe", "Daniela", "Cristóbal", "Paula", "Ignacio",
           "Fernanda", "Tomás", "Catalina", "Joaquín", "Antonia", "Benjamín"]
APELLIDOS = ["González", "Muñoz", "Rojas", "Díaz", "Pérez", "Soto", "Contreras", "Silva",
             "Martínez", "Sepúlveda", "Morales", "Rodríguez", "López", "Fuentes", "Hernández",
             "Torres", "Araya", "Flores", "Espinoza", "Valenzuela", "Castillo", "Tapia",
             "Reyes", "Gutiérrez", "Castro", "Pizarro", "Álvarez", "Vásquez", "Sánchez", "Fernández"]
CIUDADES = ["Valdivia", "Valdivia", "Valdivia", "Osorno", "Puerto Montt", "Temuco",
            "Santiago", "La Unión", "Panguipulli", "Concepción"]
VENDEDORES = ["Camila Rojas", "Matías Soto", "Francisca Muñoz", "Diego Contreras"]
JEFES_OBRA = ["Ricardo Almonacid", "Patricio Vera", "Marcela Ojeda", "Héctor Navarro", "Sandra Ibáñez"]


# ---------------------------------------------------------------- utilidades
def fecha_entre(a, b):
    return a + timedelta(days=random.randint(0, max((b - a).days, 0)))


def sin_tildes(texto):
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def rut_nuevo(usados):
    while True:
        num = random.randint(8_000_000, 24_000_000)
        suma, mult = 0, 2
        for d in reversed(str(num)):
            suma += int(d) * mult
            mult = mult + 1 if mult < 7 else 2
        r = 11 - suma % 11
        dv = "K" if r == 10 else "0" if r == 11 else str(r)
        rut = f"{num:,}".replace(",", ".") + "-" + dv
        if rut not in usados:
            usados.add(rut)
            return rut


def nueva_base(nombre_archivo, esquema):
    DATOS.mkdir(exist_ok=True)
    ruta = DATOS / nombre_archivo
    if ruta.exists():
        ruta.unlink()
    con = sqlite3.connect(ruta)
    con.executescript(esquema)
    return con


def iso(d):
    return d.isoformat() if d else None


# ------------------------------------------------------------------ comercial
ESQUEMA_COMERCIAL = """
CREATE TABLE clientes (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    rut TEXT NOT NULL UNIQUE,
    email TEXT,
    telefono TEXT,
    ciudad TEXT,
    fecha_registro TEXT  -- AAAA-MM-DD
);
CREATE TABLE proyectos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    comuna TEXT,
    tipo TEXT,               -- Casas o Departamentos
    estado TEXT,             -- En venta o Entregado
    fecha_lanzamiento TEXT   -- AAAA-MM-DD
);
CREATE TABLE unidades (
    id INTEGER PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos(id),
    numero TEXT,
    tipo TEXT,
    superficie_m2 REAL,
    dormitorios INTEGER,
    banos INTEGER,
    precio_lista_uf REAL,    -- precio de lista en UF
    estado TEXT              -- Disponible, Reservada o Vendida
);
CREATE TABLE cotizaciones (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    unidad_id INTEGER NOT NULL REFERENCES unidades(id),
    fecha TEXT,              -- AAAA-MM-DD
    vendedor TEXT,
    estado TEXT              -- Enviada, En seguimiento, Aceptada o Rechazada
);
CREATE TABLE ventas (
    id INTEGER PRIMARY KEY,
    unidad_id INTEGER NOT NULL UNIQUE REFERENCES unidades(id),
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    fecha TEXT,              -- AAAA-MM-DD
    precio_final_uf REAL,    -- precio pagado en UF
    forma_pago TEXT,         -- Credito hipotecario, Contado o Pie + credito
    vendedor TEXT
);
"""

TIPOS_CASA = [("Casa 3D2B", 3, 2, (85, 105), (3800, 4600)),
              ("Casa 4D3B", 4, 3, (110, 140), (4800, 5900))]
TIPOS_DEPTO = [("Depto 1D1B", 1, 1, (38, 48), (1900, 2400)),
               ("Depto 2D1B", 2, 1, (52, 65), (2700, 3400)),
               ("Depto 3D2B", 3, 2, (75, 92), (3900, 4800))]


def crear_comercial():
    con = nueva_base("comercial.db", ESQUEMA_COMERCIAL)

    usados, clientes = set(), []
    for i in range(1, 121):
        nombre = random.choice(NOMBRES)
        apellido1, apellido2 = random.sample(APELLIDOS, 2)
        email = sin_tildes(f"{nombre}.{apellido1}{i}".lower()) + "@correo.cl"
        clientes.append((i, f"{nombre} {apellido1} {apellido2}", rut_nuevo(usados), email,
                         f"+569{random.randint(40000000, 99999999)}", random.choice(CIUDADES),
                         iso(fecha_entre(date(2024, 1, 1), HOY))))
    con.executemany("INSERT INTO clientes VALUES (?,?,?,?,?,?,?)", clientes)

    unidades, fechas_proyecto = [], {}
    id_unidad = 0
    for id_proy, p in enumerate(PROYECTOS, 1):
        estado_proy = "Entregado" if p["avance"] == 100 else "En venta"
        con.execute("INSERT INTO proyectos VALUES (?,?,?,?,?,?)",
                    (id_proy, p["nombre"], p["comuna"], p["tipo"], estado_proy, iso(p["lanzamiento"])))
        tipos = TIPOS_CASA if p["tipo"] == "Casas" else TIPOS_DEPTO
        for n in range(1, p["unidades"] + 1):
            id_unidad += 1
            nombre_tipo, dorm, banos, sup, precio = random.choice(tipos)
            r = random.random()
            estado = ("Vendida" if r < p["vendido"]
                      else "Reservada" if r < p["vendido"] + 0.08 else "Disponible")
            unidades.append((id_unidad, id_proy, f"{n:03d}", nombre_tipo,
                             round(random.uniform(*sup), 1), dorm, banos,
                             float(round(random.randint(*precio), -1)), estado))
            fechas_proyecto[id_unidad] = p["lanzamiento"]
    con.executemany("INSERT INTO unidades VALUES (?,?,?,?,?,?,?,?,?)", unidades)

    ventas = []
    for u in unidades:
        if u[8] == "Vendida":
            ventas.append((len(ventas) + 1, u[0], random.randint(1, 120),
                           iso(fecha_entre(fechas_proyecto[u[0]] + timedelta(days=20), HOY)),
                           round(u[7] * random.uniform(0.94, 1.0), 1),
                           random.choice(["Crédito hipotecario", "Contado", "Pie + crédito"]),
                           random.choice(VENDEDORES)))
    con.executemany("INSERT INTO ventas VALUES (?,?,?,?,?,?,?)", ventas)

    cotizaciones = []
    for i in range(1, 221):
        u = random.choice(unidades)
        cotizaciones.append((i, random.randint(1, 120), u[0],
                             iso(fecha_entre(fechas_proyecto[u[0]], HOY)),
                             random.choice(VENDEDORES),
                             random.choices(["Enviada", "En seguimiento", "Aceptada", "Rechazada"],
                                            weights=[30, 35, 15, 20])[0]))
    con.executemany("INSERT INTO cotizaciones VALUES (?,?,?,?,?,?)", cotizaciones)

    con.commit()
    con.close()


# ------------------------------------------------------ finanzas y operaciones
ESQUEMA_FINANZAS = """
CREATE TABLE proveedores (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    rut TEXT NOT NULL UNIQUE,
    rubro TEXT
);
CREATE TABLE presupuestos (
    id INTEGER PRIMARY KEY,
    proyecto TEXT NOT NULL,
    anio INTEGER NOT NULL,
    categoria TEXT NOT NULL,   -- Terreno, Obra gruesa, Terminaciones, Instalaciones, Marketing o Administracion
    presupuestado_clp INTEGER, -- monto aprobado en pesos
    ejecutado_clp INTEGER      -- monto gastado a la fecha en pesos
);
CREATE TABLE facturas (
    id INTEGER PRIMARY KEY,
    proveedor_id INTEGER NOT NULL REFERENCES proveedores(id),
    proyecto TEXT NOT NULL,
    numero TEXT NOT NULL,
    fecha_emision TEXT,        -- AAAA-MM-DD
    fecha_vencimiento TEXT,    -- AAAA-MM-DD
    monto_clp INTEGER,
    estado TEXT                -- Pagada, Pendiente o Vencida
);
CREATE TABLE pagos (
    id INTEGER PRIMARY KEY,
    factura_id INTEGER NOT NULL REFERENCES facturas(id),
    fecha_pago TEXT,           -- AAAA-MM-DD
    monto_clp INTEGER,
    medio TEXT                 -- Transferencia, Cheque o Vale vista
);
CREATE TABLE flujo_caja (
    id INTEGER PRIMARY KEY,
    mes TEXT NOT NULL,         -- AAAA-MM
    ingresos_clp INTEGER,
    egresos_clp INTEGER,
    saldo_clp INTEGER          -- saldo acumulado al cierre del mes
);
"""

PROVEEDORES = [
    ("Constructora Sur Ltda.", "Obra gruesa"), ("Hormigones del Sur", "Hormigón"),
    ("Ferretería Industrial Valdivia", "Materiales"),
    ("Electro Instalaciones Calle-Calle", "Electricidad"),
    ("Sanitarios y Gas Los Ríos", "Instalaciones sanitarias"),
    ("Carpintería Austral", "Terminaciones"), ("Estudio Arquitectura Rivera", "Diseño"),
    ("Aceros del Pacífico", "Acero"), ("Publicidad Sur Creativo", "Marketing"),
    ("Topografía y Suelos Ltda.", "Estudios"), ("Seguridad Obra Segura", "Prevención de riesgos"),
    ("Arriendo de Maquinaria Patagonia", "Maquinaria"),
]
CATEGORIAS = {"Terreno": (400, 900), "Obra gruesa": (900, 2000), "Terminaciones": (500, 1200),
              "Instalaciones": (300, 800), "Marketing": (40, 120), "Administración": (80, 200)}


def crear_finanzas():
    con = nueva_base("finanzas_operaciones.db", ESQUEMA_FINANZAS)

    usados = set()
    con.executemany("INSERT INTO proveedores VALUES (?,?,?,?)",
                    [(i, n, rut_nuevo(usados), r) for i, (n, r) in enumerate(PROVEEDORES, 1)])

    filas, id_p = [], 0
    for p in PROYECTOS:
        for anio in (2025, 2026):
            for categoria, (lo, hi) in CATEGORIAS.items():
                id_p += 1
                presup = random.randint(lo, hi) * 1_000_000
                factor = random.uniform(0.55, 1.08) if anio == 2025 else random.uniform(0.25, 0.80)
                filas.append((id_p, p["nombre"], anio, categoria, presup, int(presup * factor)))
    con.executemany("INSERT INTO presupuestos VALUES (?,?,?,?,?,?)", filas)

    facturas, pagos = [], []
    for i in range(1, 161):
        emision = fecha_entre(date(2025, 6, 1), HOY)
        vencimiento = emision + timedelta(days=30)
        monto = random.randint(3_000, 120_000) * 1000
        fecha_pago = emision + timedelta(days=random.randint(5, 45))
        if random.random() < 0.70 and fecha_pago <= HOY:
            estado = "Pagada"
            pagos.append((len(pagos) + 1, i, iso(fecha_pago), monto,
                          random.choice(["Transferencia", "Transferencia", "Cheque", "Vale vista"])))
        else:
            estado = "Vencida" if vencimiento < HOY else "Pendiente"
        facturas.append((i, random.randint(1, len(PROVEEDORES)), random.choice(PROYECTOS)["nombre"],
                         f"F-{1000 + i}", iso(emision), iso(vencimiento), monto, estado))
    con.executemany("INSERT INTO facturas VALUES (?,?,?,?,?,?,?,?)", facturas)
    con.executemany("INSERT INTO pagos VALUES (?,?,?,?,?)", pagos)

    flujo, saldo, anio, mes = [], 350_000_000, 2025, 11
    for i in range(1, 13):
        ingresos = random.randint(250, 520) * 1_000_000
        egresos = random.randint(220, 480) * 1_000_000
        saldo += ingresos - egresos
        flujo.append((i, f"{anio}-{mes:02d}", ingresos, egresos, saldo))
        mes += 1
        if mes == 13:
            anio, mes = anio + 1, 1
    con.executemany("INSERT INTO flujo_caja VALUES (?,?,?,?,?)", flujo)

    con.commit()
    con.close()


# --------------------------------------------------------------------- tecnica
ESQUEMA_TECNICA = """
CREATE TABLE obras (
    id INTEGER PRIMARY KEY,
    proyecto TEXT NOT NULL,
    comuna TEXT,
    etapa_actual TEXT,
    avance_pct REAL,                 -- avance total, 0 a 100
    fecha_inicio TEXT,               -- AAAA-MM-DD
    fecha_termino_estimada TEXT,     -- AAAA-MM-DD
    jefe_obra TEXT
);
CREATE TABLE contratistas (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    especialidad TEXT
);
CREATE TABLE etapas (
    id INTEGER PRIMARY KEY,
    obra_id INTEGER NOT NULL REFERENCES obras(id),
    nombre TEXT NOT NULL,            -- Movimiento de tierras, Fundaciones, Obra gruesa, Instalaciones, Terminaciones o Entrega
    estado TEXT,                     -- Pendiente, En curso o Terminada
    avance_pct REAL,                 -- avance de la etapa, 0 a 100
    fecha_inicio TEXT,               -- planificada, AAAA-MM-DD
    fecha_fin TEXT,                  -- planificada, AAAA-MM-DD
    contratista_id INTEGER REFERENCES contratistas(id)
);
CREATE TABLE inspecciones (
    id INTEGER PRIMARY KEY,
    obra_id INTEGER NOT NULL REFERENCES obras(id),
    fecha TEXT,                      -- AAAA-MM-DD
    tipo TEXT,                       -- Seguridad, Calidad, Municipal o Estructural
    resultado TEXT,                  -- Aprobada, Aprobada con observaciones o Rechazada
    observaciones TEXT
);
CREATE TABLE permisos (
    id INTEGER PRIMARY KEY,
    obra_id INTEGER NOT NULL REFERENCES obras(id),
    tipo TEXT,
    numero TEXT,
    fecha_solicitud TEXT,            -- AAAA-MM-DD, vacio si aun no se solicita
    fecha_aprobacion TEXT,           -- AAAA-MM-DD, vacio si no esta aprobado
    estado TEXT                      -- Aprobado, En tramite o Pendiente
);
"""

ETAPAS = ["Movimiento de tierras", "Fundaciones", "Obra gruesa", "Instalaciones",
          "Terminaciones", "Entrega"]
CORTES = [0, 8, 25, 55, 78, 95, 100]  # porcentaje de avance total donde empieza y termina cada etapa
CONTRATISTAS = [
    ("Excavaciones Valdivia", "Movimiento de tierras"), ("Fundaciones Austral", "Fundaciones"),
    ("Hormigonera Calle-Calle", "Obra gruesa"), ("Estructuras del Sur", "Obra gruesa"),
    ("Electro Instalaciones Calle-Calle", "Instalaciones"),
    ("Sanitarios y Gas Los Ríos", "Instalaciones"),
    ("Carpintería Austral", "Terminaciones"), ("Pinturas Ruka", "Terminaciones"),
]
OBSERVACIONES = {
    "Aprobada": ["Sin observaciones", "Cumple con lo proyectado", "Trabajos conformes a planos"],
    "Aprobada con observaciones": ["Falta señalética en acceso", "Armaduras con recubrimiento justo",
                                   "Orden y aseo deficiente en bodega", "Registro de EPP incompleto"],
    "Rechazada": ["Hormigón bajo la resistencia especificada", "Andamios sin certificación",
                  "Instalación eléctrica fuera de norma"],
}


def crear_tecnica():
    con = nueva_base("tecnica.db", ESQUEMA_TECNICA)

    con.executemany("INSERT INTO contratistas VALUES (?,?,?)",
                    [(i, n, e) for i, (n, e) in enumerate(CONTRATISTAS, 1)])
    por_especialidad = {}
    for i, (_, esp) in enumerate(CONTRATISTAS, 1):
        por_especialidad.setdefault(esp, []).append(i)

    id_etapa = id_insp = id_perm = 0
    for id_obra, p in enumerate(PROYECTOS, 1):
        avance = p["avance"]
        total = (p["termino"] - p["inicio_obra"]).days
        etapas = []
        for k, nombre in enumerate(ETAPAS):
            a, b = CORTES[k], CORTES[k + 1]
            pct = max(0.0, min(100.0, (avance - a) / (b - a) * 100))
            estado = "Terminada" if pct >= 100 else "En curso" if pct > 0 else "Pendiente"
            ini = p["inicio_obra"] + timedelta(days=int(total * a / 100))
            fin = p["inicio_obra"] + timedelta(days=int(total * b / 100))
            contratista = (random.choice(por_especialidad[nombre])
                           if nombre in por_especialidad else None)
            id_etapa += 1
            etapas.append((id_etapa, id_obra, nombre, estado, round(pct, 1), iso(ini), iso(fin), contratista))
        actual = next((e[2] for e in etapas if e[3] != "Terminada"), "Entregada")
        con.execute("INSERT INTO obras VALUES (?,?,?,?,?,?,?,?)",
                    (id_obra, p["nombre"], p["comuna"], actual, float(avance), iso(p["inicio_obra"]),
                     iso(p["termino"]), JEFES_OBRA[id_obra - 1]))
        con.executemany("INSERT INTO etapas VALUES (?,?,?,?,?,?,?,?)", etapas)

        for _ in range(random.randint(6, 10)):
            id_insp += 1
            resultado = random.choices(list(OBSERVACIONES), weights=[55, 33, 12])[0]
            con.execute("INSERT INTO inspecciones VALUES (?,?,?,?,?,?)",
                        (id_insp, id_obra, iso(fecha_entre(p["inicio_obra"], min(HOY, p["termino"]))),
                         random.choice(["Seguridad", "Calidad", "Municipal", "Estructural"]),
                         resultado, random.choice(OBSERVACIONES[resultado])))

        permisos = [
            ("Factibilidad sanitaria", p["inicio_obra"] - timedelta(days=200), 60),
            ("Permiso de edificación", p["inicio_obra"] - timedelta(days=150), 70),
            ("Aviso de inicio de obra", p["inicio_obra"] - timedelta(days=10), 5),
        ]
        for tipo, solicitud, dias in permisos:
            id_perm += 1
            con.execute("INSERT INTO permisos VALUES (?,?,?,?,?,?,?)",
                        (id_perm, id_obra, tipo, f"{random.randint(100, 999)}/{solicitud.year}",
                         iso(solicitud), iso(solicitud + timedelta(days=dias)), "Aprobado"))
        id_perm += 1
        if avance == 100:
            con.execute("INSERT INTO permisos VALUES (?,?,?,?,?,?,?)",
                        (id_perm, id_obra, "Recepción final", f"{random.randint(100, 999)}/2026",
                         iso(p["termino"] - timedelta(days=20)), iso(p["termino"] + timedelta(days=10)),
                         "Aprobado"))
        elif avance >= 70:
            con.execute("INSERT INTO permisos VALUES (?,?,?,?,?,?,?)",
                        (id_perm, id_obra, "Recepción final", None, iso(HOY - timedelta(days=15)),
                         None, "En tramite"))
        else:
            con.execute("INSERT INTO permisos VALUES (?,?,?,?,?,?,?)",
                        (id_perm, id_obra, "Recepción final", None, None, None, "Pendiente"))

    con.commit()
    con.close()


if __name__ == "__main__":
    crear_comercial()
    crear_finanzas()
    crear_tecnica()
    for area in AREAS.values():
        print(f"Creada {area['db'].name} ({area['nombre']})")

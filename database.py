import sqlite3  # Importa el módulo SQLite para la base de datos ligera en archivo.
import time
from datetime import datetime  # Para fechas en los datos iniciales.
from werkzeug.security import generate_password_hash  # Función para hashear contraseñas.

DATABASE = "la_gacela_nom035.db"  # Nombre del archivo de base de datos SQLite para La Gacela.


def get_db():
    """Abre una conexión SQLite y devuelve el objeto de conexión."""
    conexion = sqlite3.connect(DATABASE, timeout=30)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA busy_timeout = 30000")
    conexion.execute("PRAGMA journal_mode = WAL")
    conexion.execute("PRAGMA synchronous = NORMAL")
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def query_db(query, args=(), one=False):
    """Ejecuta una consulta SQL y devuelve resultados como diccionarios."""
    conexion = get_db()
    try:
        cursor = conexion.execute(query, args)
        filas = cursor.fetchall()
        conexion.commit()
        resultados = [dict(fila) for fila in filas]
        if one:
            return resultados[0] if resultados else None
        return resultados
    finally:
        conexion.close()


def init_db():
    """Crea las tablas necesarias y datos iniciales si no existen."""
    def ensure_columns(cursor, table, cols):
        cursor.execute(f"PRAGMA table_info({table})")
        existing = [row[1] for row in cursor.fetchall()]
        for name, definition in cols.items():
            if name not in existing:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    def setup_schema(cursor):
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                nombre_completo TEXT,
                departamento TEXT,
                puesto TEXT,
                fecha_ingreso DATE,
                estado_laboral TEXT DEFAULT 'activo',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        ensure_columns(cursor, 'users', {
            'email': 'TEXT',
            'nombre_completo': 'TEXT',
            'departamento': 'TEXT',
            'puesto': 'TEXT',
            'fecha_ingreso': 'DATE',
            "estado_laboral": "TEXT DEFAULT 'activo'",
            'created_at': 'TIMESTAMP'
        })

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS centros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                razon_social TEXT NOT NULL,
                domicilio TEXT NOT NULL,
                actividad_principal TEXT NOT NULL,
                total_trabajadores INTEGER NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                centro_id INTEGER NOT NULL,
                tipo_guia TEXT NOT NULL,
                datos_json TEXT NOT NULL,
                puntaje INTEGER,
                nivel_riesgo TEXT,
                acciones_necesarias TEXT,
                fecha TEXT NOT NULL,
                FOREIGN KEY (centro_id) REFERENCES centros(id)
            )
            """
        )
        # Garantizar columna adicional si se actualiza esquema en caliente
        ensure_columns(cursor, 'evaluaciones', {
            'acciones_necesarias': 'TEXT'
        })

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cuestionarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                tipo TEXT,
                activo INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS preguntas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cuestionario_id INTEGER NOT NULL,
                pregunta TEXT NOT NULL,
                tipo TEXT,
                opciones TEXT,
                orden INTEGER,
                FOREIGN KEY (cuestionario_id) REFERENCES cuestionarios (id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS respuestas_encuesta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empleado_id INTEGER NOT NULL,
                cuestionario_id INTEGER NOT NULL,
                pregunta_id INTEGER NOT NULL,
                respuesta TEXT,
                fecha_respuesta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (empleado_id) REFERENCES users (id),
                FOREIGN KEY (cuestionario_id) REFERENCES cuestionarios (id),
                FOREIGN KEY (pregunta_id) REFERENCES preguntas (id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS denuncias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empleado_id INTEGER,
                tipo_denuncia TEXT,
                descripcion TEXT,
                fecha_evento DATE,
                evidencia TEXT,
                estado TEXT DEFAULT 'pendiente',
                confidencial INTEGER DEFAULT 1,
                fecha_denuncia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_resolucion TIMESTAMP,
                acciones_tomadas TEXT,
                FOREIGN KEY (empleado_id) REFERENCES users (id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS capacitaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descripcion TEXT,
                contenido TEXT,
                fecha_inicio DATE,
                fecha_fin DATE,
                responsable_id INTEGER,
                dirigido_a TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (responsable_id) REFERENCES users (id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS asistencia_capacitacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capacitacion_id INTEGER NOT NULL,
                empleado_id INTEGER NOT NULL,
                asistio INTEGER DEFAULT 0,
                calificacion REAL,
                fecha_asistencia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (capacitacion_id) REFERENCES capacitaciones (id),
                FOREIGN KEY (empleado_id) REFERENCES users (id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS indicadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empleado_id INTEGER NOT NULL,
                nivel_estres REAL,
                clima_laboral REAL,
                satisfaccion REAL,
                riesgo_rotacion INTEGER,
                factores_riesgo TEXT,
                recomendaciones TEXT,
                fecha_evaluacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (empleado_id) REFERENCES users (id)
            )
            """
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO users (username, password_hash, role, email, nombre_completo, departamento, puesto)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("admin", generate_password_hash("admin123"), "admin", "admin@lagacela.mx", "Administrador Sistema", "Sistemas", "Gerente TI"),
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO users (username, password_hash, role, email, nombre_completo, departamento, puesto)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("rrhh", generate_password_hash("rrhh123"), "recursos_humanos", "rrhh@lagacela.mx", "Especialista RRHH", "Recursos Humanos", "Especialista Bienestar"),
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO users (username, password_hash, role, email, nombre_completo, departamento, puesto)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("empleado", generate_password_hash("emp123"), "empleado", "empleado@lagacela.mx", "Juan Pérez Gómez", "Producción", "Operario"),
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO centros (razon_social, domicilio, actividad_principal, total_trabajadores)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Manufacturera de Ropa La Gacela",
                "Carretera Industrial 123, Parque Textil, Estado de México",
                "Fabricación de prendas de vestir y confección industrial",
                120,
            ),
        )

        cursor.execute("SELECT COUNT(*) FROM cuestionarios")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO cuestionarios (nombre, descripcion, tipo, activo) VALUES (?, ?, ?, 1)",
                (
                    "Encuesta NOM-035 sobre factores psicosociales",
                    "Cuestionario breve para identificar riesgos psicosociales en el lugar de trabajo.",
                    "nom035",
                ),
            )
            cuestionario_id = cursor.lastrowid
            preguntas_iniciales = [
                ("¿Siente presión excesiva para cumplir tareas en su jornada de trabajo?", "si_no", "si,no"),
                ("¿Percibe que su carga de trabajo supera sus capacidades habituales?", "si_no", "si,no"),
                ("¿Recibe apoyo suficiente de su jefe o compañeros cuando lo necesita?", "si_no", "si,no"),
                ("¿Considera que el ambiente de trabajo es respetuoso y libre de acoso?", "si_no", "si,no"),
                ("¿Ha identificado condiciones que afectan su seguridad o salud emocional en el trabajo?", "si_no", "si,no"),
            ]
            for orden, (pregunta, tipo, opciones) in enumerate(preguntas_iniciales, start=1):
                cursor.execute(
                    "INSERT INTO preguntas (cuestionario_id, pregunta, tipo, opciones, orden) VALUES (?, ?, ?, ?, ?)",
                    (cuestionario_id, pregunta, tipo, opciones, orden),
                )

        cursor.execute("SELECT COUNT(*) FROM capacitaciones")
        if cursor.fetchone()[0] == 0:
            cursor.execute("SELECT id FROM users WHERE username = ?", ("rrhh",))
            rrhh_user = cursor.fetchone()
            responsable_id = rrhh_user[0] if rrhh_user else None
            cursor.execute(
                "INSERT INTO capacitaciones (titulo, descripcion, contenido, fecha_inicio, fecha_fin, responsable_id, dirigido_a) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    "Jornada de sensibilización NOM-035",
                    "Capacitación para reconocer y gestionar factores de riesgo psicosocial en el trabajo.",
                    "Contenido de sensibilización sobre estrés, clima laboral y medidas preventivas.",
                    datetime.now().date().isoformat(),
                    (datetime.now().date()).isoformat(),
                    responsable_id,
                    "Todos los empleados",
                ),
            )

    max_attempts = 5
    last_exception = None
    for attempt in range(1, max_attempts + 1):
        try:
            with get_db() as conexion:
                setup_schema(conexion.cursor())
            return
        except sqlite3.OperationalError as exc:
            last_exception = exc
            if 'locked' in str(exc).lower() and attempt < max_attempts:
                time.sleep(1)
                continue
            raise
    if last_exception:
        raise last_exception


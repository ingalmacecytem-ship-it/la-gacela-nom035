import sqlite3  # Importa el módulo SQLite para la base de datos ligera en archivo.
from werkzeug.security import generate_password_hash  # Función para hashear contraseñas.

DATABASE = "la_gacela_nom035.db"  # Nombre del archivo de base de datos SQLite para La Gacela.


def get_db():
    """Abre una conexión SQLite y devuelve el objeto de conexión."""
    conexion = sqlite3.connect(DATABASE)  # Conecta al archivo de base de datos.
    conexion.row_factory = sqlite3.Row  # Permite acceder a filas por nombre de columna.
    return conexion  # Devuelve la conexión para uso en consultas.


def init_db():
    """Crea las tablas necesarias y datos iniciales si no existen."""
    conexion = get_db()  # Inicia conexión SQLite.
    cursor = conexion.cursor()  # Crea cursor para ejecutar comandos SQL.

    # Tabla de usuarios con roles y contraseñas.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """
    )

    # Tabla de centros de trabajo registrados.
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

    # Tabla de evaluaciones realizadas, incluyendo tipo y resultados.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            centro_id INTEGER NOT NULL,
            tipo_guia TEXT NOT NULL,
            datos_json TEXT NOT NULL,
            puntaje INTEGER,
            nivel_riesgo TEXT,
            fecha TEXT NOT NULL,
            FOREIGN KEY (centro_id) REFERENCES centros(id)
        )
        """
    )

    # Inserta usuario administrador inicial si no existe.
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (username, password_hash, role)
        VALUES (?, ?, ?)
        """,
        ("admin", generate_password_hash("admin123"), "admin"),
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

    conexion.commit()  # Guardar los cambios en el archivo de base de datos.
    conexion.close()  # Cerrar la conexión.


def query_db(query, args=(), one=False):
    """Ejecuta una consulta SQL y devuelve resultados opcionales."""
    conexion = get_db()  # Abre conexión nueva para la consulta.
    cursor = conexion.execute(query, args)  # Ejecuta SQL parametrizado.
    rv = cursor.fetchall()  # Obtiene todas las filas resultantes.
    conexion.commit()  # Guarda cambios si hay.
    conexion.close()  # Cierra enlace con el archivo.
    return (rv[0] if rv else None) if one else rv  # Retorna una fila o lista.

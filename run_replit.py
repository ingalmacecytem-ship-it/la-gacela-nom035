import os  # Para leer variables de entorno configuradas por Replit.
from app import app  # Importa la aplicación Flask definida en app.py.
import database  # Importa la configuración de base de datos.

# Inicializa la base de datos al iniciar Replit.
database.init_db()

if __name__ == "__main__":
    host = os.environ.get("IP", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ["1", "true", "yes"]
    app.run(host=host, port=port, debug=debug)

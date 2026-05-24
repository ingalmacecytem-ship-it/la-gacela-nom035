from pathlib import Path

p = Path('app.py')
text = p.read_text(encoding='utf-8')
text = text.replace(
    'import json  # Para manejar serialización de datos en JSON.\nfrom datetime import datetime  # Para manejar fechas de evaluaciones.\nfrom functools import wraps  # Para crear decoradores personalizados.\nfrom flask import (\n',
    'import os  # Para leer variables de entorno como PORT.\nimport json  # Para manejar serialización de datos en JSON.\nfrom datetime import datetime  # Para manejar fechas de evaluaciones.\nfrom functools import wraps  # Para crear decoradores personalizados.\nfrom flask import (\n'
)
text = text.replace(
    'if __name__ == "__main__":\n    database.init_db()  # Inicializa la base de datos al arrancar la app.\n    app.run(debug=True)  # Ejecuta el servidor en modo de desarrollo.\n',
    'if __name__ == "__main__":\n    database.init_db()  # Inicializa la base de datos al arrancar la app.\n    host = os.environ.get("IP", "0.0.0.0")\n    port = int(os.environ.get("PORT", 5000))\n    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ["1", "true", "yes"]\n    app.run(host=host, port=port, debug=debug)\n'
)
p.write_text(text, encoding='utf-8')

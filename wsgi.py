from app import app

# Punto de entrada WSGI para servidores compatibles.
# Ejemplo de uso en hosting: waitress-serve --listen=*:8000 wsgi:app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

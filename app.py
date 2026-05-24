import os  # Para leer variables de entorno como PORT.
import json  # Para manejar serialización de datos en JSON.
from datetime import datetime  # Para manejar fechas de evaluaciones.
from functools import wraps  # Para crear decoradores personalizados.
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    jsonify,
    send_from_directory,
)
import database  # Importa funciones de base de datos locales.
from werkzeug.security import check_password_hash  # Para verificar contraseñas seguras.
from utils import crear_pdf_evaluacion, crear_excel_resumen  # Funciones de exportación.

app = Flask(__name__)  # Crea la aplicación Flask.
app.config["SECRET_KEY"] = "nom035_secret_2026"  # Clave para sesiones seguras.

def login_required(role=None):
    """Decorador para proteger rutas que requieran sesión y rol."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                return render_template("error.html", mensaje="Acceso no autorizado."), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator


@app.route("/")
def home():
    """Página de inicio que redirige al dashboard o al login."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Formulario de inicio de sesión y validación de credenciales."""
    error = None
    if request.method == "POST":
        username = request.form["username"]  # Usuario enviado desde el formulario.
        password = request.form["password"]  # Contraseña enviada desde el formulario.

        usuario = database.query_db(
            "SELECT * FROM users WHERE username = ?",
            (username,),
            one=True,
        )

        if usuario and check_password_hash(usuario["password_hash"], password):
            session["user_id"] = usuario["id"]  # Guarda ID de usuario en sesión.
            session["username"] = usuario["username"]  # Guarda nombre de usuario.
            session["role"] = usuario["role"]  # Guarda rol del usuario.
            return redirect(url_for("dashboard"))

        error = "Usuario o contraseña incorrectos."  # Mensaje de error.

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """Termina la sesión del usuario."""
    session.clear()  # Borra todos los datos de sesión.
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required()
def dashboard():
    """Muestra el dashboard con métricas de NOM-035."""
    total_centros = database.query_db("SELECT COUNT(*) AS total FROM centros", one=True)["total"]
    total_evaluaciones = database.query_db("SELECT COUNT(*) AS total FROM evaluaciones", one=True)["total"]
    niveles_raw = database.query_db(
        "SELECT nivel_riesgo, COUNT(*) AS total FROM evaluaciones GROUP BY nivel_riesgo"
    )
    niveles = [dict(item) for item in niveles_raw]  # Convierte filas SQLite en diccionarios JSON serializables.

    roles = {
        "admin": "Administrador",
        "evaluador": "Evaluador",
        "inspector": "Inspector",
    }

    return render_template(
        "dashboard.html",
        total_centros=total_centros,
        total_evaluaciones=total_evaluaciones,
        niveles=niveles,
        role=session.get("role"),
        roles=roles,
    )


@app.route("/registrar-centro", methods=["GET", "POST"])
@login_required()
def registrar_centro():
    """Registra un centro de trabajo en la base de datos."""
    mensaje = None
    if request.method == "POST":
        razon_social = request.form["razon_social"]
        domicilio = request.form["domicilio"]
        actividad_principal = request.form["actividad_principal"]
        total_trabajadores = int(request.form["total_trabajadores"])

        database.query_db(
            "INSERT INTO centros (razon_social, domicilio, actividad_principal, total_trabajadores) VALUES (?, ?, ?, ?)",
            (razon_social, domicilio, actividad_principal, total_trabajadores),
        )

        mensaje = "Centro de trabajo registrado correctamente."

    return render_template("registrar_centro.html", mensaje=mensaje)


@app.route("/evaluacion", methods=["GET", "POST"])
@login_required()
def evaluacion():
    """Proceso de registro y cálculo de evaluaciones NOM-035."""
    mensaje = None
    centros = database.query_db("SELECT * FROM centros ORDER BY razon_social")

    if request.method == "POST":
        centro_id = int(request.form["centro_id"])
        tipo_guia = request.form["tipo_guia"]
        datos = {
            "pregunta_1": request.form.get("pregunta_1", ""),
            "pregunta_2": request.form.get("pregunta_2", ""),
            "pregunta_3": request.form.get("pregunta_3", ""),
            "comentarios": request.form.get("comentarios", ""),
        }

        puntaje = 0
        nivel_riesgo = "Nulo o despreciable"

        if tipo_guia == "II":
            puntaje = sum(
                int(request.form.get(f"item_{i}", 0)) for i in range(1, 11)
            )
            if puntaje < 20:
                nivel_riesgo = "Nulo o despreciable"
            elif puntaje < 45:
                nivel_riesgo = "Bajo"
            elif puntaje < 70:
                nivel_riesgo = "Medio"
            elif puntaje < 90:
                nivel_riesgo = "Alto"
            else:
                nivel_riesgo = "Muy alto"

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        database.query_db(
            "INSERT INTO evaluaciones (centro_id, tipo_guia, datos_json, puntaje, nivel_riesgo, fecha) VALUES (?, ?, ?, ?, ?, ?)",
            (centro_id, tipo_guia, json.dumps(datos, ensure_ascii=False), puntaje, nivel_riesgo, fecha),
        )

        mensaje = "Evaluación registrada y guardada correctamente."

    return render_template("evaluacion.html", centros=centros, mensaje=mensaje)


@app.route("/reporte/pdf/<int:evaluacion_id>")
@login_required()
def reporte_pdf(evaluacion_id):
    """Genera un reporte PDF para una evaluación específica."""
    evaluacion = database.query_db(
        "SELECT e.*, c.razon_social, c.domicilio, c.actividad_principal, c.total_trabajadores FROM evaluaciones e JOIN centros c ON e.centro_id = c.id WHERE e.id = ?",
        (evaluacion_id,),
        one=True,
    )

    if not evaluacion:
        return render_template("error.html", mensaje="Evaluación no encontrada."), 404

    pdf_buffer = crear_pdf_evaluacion(evaluacion, evaluacion)  # Usa los datos combinados.
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"reporte_la_gacela_{evaluacion_id}.pdf",
        mimetype="application/pdf",
    )


@app.route("/reporte/excel")
@login_required(role="admin")
def reporte_excel():
    """Genera un archivo Excel con todas las evaluaciones."""
    evaluaciones = database.query_db(
        "SELECT e.*, c.razon_social FROM evaluaciones e JOIN centros c ON e.centro_id = c.id"
    )
    excel_buffer = crear_excel_resumen(evaluaciones)
    return send_file(
        excel_buffer,
        as_attachment=True,
        download_name="evaluaciones_la_gacela.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/api/login", methods=["POST"])
def api_login():
    """Endpoint API para iniciar sesión desde una app móvil."""
    datos = request.get_json() or {}
    username = datos.get("username", "")
    password = datos.get("password", "")

    usuario = database.query_db(
        "SELECT * FROM users WHERE username = ?",
        (username,),
        one=True,
    )

    if usuario and check_password_hash(usuario["password_hash"], password):
        return jsonify({"success": True, "role": usuario["role"]})

    return jsonify({"success": False, "message": "Usuario o contraseña incorrectos."}), 401


@app.route("/api/evaluacion", methods=["POST"])
def api_evaluacion():
    """Endpoint API para registrar una evaluación desde una app móvil."""
    datos = request.get_json() or {}
    centro_id = datos.get("centro_id")
    tipo_guia = datos.get("tipo_guia")
    contenido = datos.get("datos", {})

    if not centro_id or not tipo_guia:
        return jsonify({"success": False, "message": "Parámetros insuficientes."}), 400

    puntaje = contenido.get("puntaje", 0)
    nivel_riesgo = contenido.get("nivel_riesgo", "Nulo o despreciable")
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    database.query_db(
        "INSERT INTO evaluaciones (centro_id, tipo_guia, datos_json, puntaje, nivel_riesgo, fecha) VALUES (?, ?, ?, ?, ?, ?)",
        (centro_id, tipo_guia, json.dumps(contenido, ensure_ascii=False), puntaje, nivel_riesgo, fecha),
    )

    return jsonify({"success": True, "message": "Evaluación registrada con éxito."})


@app.route("/app")
def pwa_app():
    """Sirve la aplicación web/PWA desde el directorio web_app."""
    return send_from_directory("web_app", "index.html")


@app.route("/app/<path:path>")
def pwa_static(path):
    """Sirve los archivos estáticos para la aplicación web/PWA."""
    return send_from_directory("web_app", path)


@app.route("/api/centros", methods=["GET", "POST"])
def api_centros():
    """Endpoint para listar o registrar centros de trabajo."""
    if request.method == "GET":
        centros = database.query_db("SELECT * FROM centros ORDER BY razon_social")
        return jsonify([dict(centro) for centro in centros])

    datos = request.get_json() or {}
    razon_social = datos.get("razon_social")
    domicilio = datos.get("domicilio")
    actividad_principal = datos.get("actividad_principal")
    total_trabajadores = datos.get("total_trabajadores")

    if not razon_social or not domicilio or not actividad_principal or not total_trabajadores:
        return jsonify({"success": False, "message": "Faltan datos para registrar el centro."}), 400

    database.query_db(
        "INSERT INTO centros (razon_social, domicilio, actividad_principal, total_trabajadores) VALUES (?, ?, ?, ?)",
        (razon_social, domicilio, actividad_principal, int(total_trabajadores)),
    )
    return jsonify({"success": True, "message": "Centro de trabajo registrado."})


@app.route("/api/evaluaciones", methods=["GET"])
def api_evaluaciones():
    """Endpoint para listar las evaluaciones guardadas."""
    evaluaciones = database.query_db(
        "SELECT e.id, e.centro_id, c.razon_social, e.tipo_guia, e.datos_json, e.puntaje, e.nivel_riesgo, e.fecha "
        "FROM evaluaciones e JOIN centros c ON e.centro_id = c.id ORDER BY e.fecha DESC"
    )
    resultado = []
    for eval_item in evaluaciones:
        item = dict(eval_item)
        item["datos_json"] = json.loads(item["datos_json"])
        resultado.append(item)
    return jsonify(resultado)


@app.route("/api/reporte/pdf/<int:evaluacion_id>")
def api_reporte_pdf(evaluacion_id):
    """Genera un PDF desde la API para una evaluación específica."""
    evaluacion = database.query_db(
        "SELECT e.*, c.razon_social, c.domicilio, c.actividad_principal, c.total_trabajadores FROM evaluaciones e JOIN centros c ON e.centro_id = c.id WHERE e.id = ?",
        (evaluacion_id,),
        one=True,
    )

    if not evaluacion:
        return jsonify({"success": False, "message": "Evaluación no encontrada."}), 404

    pdf_buffer = crear_pdf_evaluacion(evaluacion, evaluacion)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"reporte_la_gacela_{evaluacion_id}.pdf",
        mimetype="application/pdf",
    )


@app.route("/api/reporte/excel")
def api_reporte_excel():
    """Genera un Excel desde la API con todas las evaluaciones."""
    evaluaciones = database.query_db(
        "SELECT e.*, c.razon_social FROM evaluaciones e JOIN centros c ON e.centro_id = c.id"
    )
    excel_buffer = crear_excel_resumen(evaluaciones)
    return send_file(
        excel_buffer,
        as_attachment=True,
        download_name="evaluaciones_la_gacela.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.errorhandler(404)
def page_not_found(error):
    """Muestra una página de error 404 personalizada."""
    return render_template("error.html", mensaje="Página no encontrada."), 404


if __name__ == "__main__":
    database.init_db()  # Inicializa la base de datos al arrancar la app.
    host = os.environ.get("IP", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ["1", "true", "yes"]
    app.run(host=host, port=port, debug=debug)

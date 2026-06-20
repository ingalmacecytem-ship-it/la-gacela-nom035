import os
import json
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify, send_from_directory
import database
from werkzeug.security import check_password_hash, generate_password_hash
from utils import crear_pdf_evaluacion, crear_excel_resumen

app = Flask(__name__)
app.config["SECRET_KEY"] = "nom035_secret_2026_lagacela"

# ==================== DECORADORES ====================

def login_required(role=None):
    """Protege rutas que requieren autenticación y rol específico."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") not in (role, "admin"):
                return render_template("error.html", mensaje="Acceso no autorizado"), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        usuario = database.query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
        if usuario and check_password_hash(usuario["password_hash"], password):
            session["user_id"] = usuario["id"]
            session["username"] = usuario["username"]
            session["role"] = usuario["role"]
            session["nombre_completo"] = usuario["nombre_completo"]
            return redirect(url_for("dashboard"))
        error = "Usuario o contraseña incorrectos"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ==================== DASHBOARD ====================

@app.route("/dashboard")
@login_required()
def dashboard():
    """Dashboard personalizado según rol del usuario."""
    role = session.get("role")
    
    if role == "recursos_humanos":
        return dashboard_rrhh()
    elif role == "empleado":
        return dashboard_empleado()
    else:
        return dashboard_admin()

def dashboard_admin():
    """Dashboard para administrador."""
    total_empleados = database.query_db("SELECT COUNT(*) AS total FROM users WHERE role='empleado'", one=True)["total"]
    total_encuestas = database.query_db("SELECT COUNT(*) AS total FROM respuestas_encuesta", one=True)["total"]
    total_denuncias = database.query_db("SELECT COUNT(*) AS total FROM denuncias", one=True)["total"]
    total_capacitaciones = database.query_db("SELECT COUNT(*) AS total FROM capacitaciones", one=True)["total"]
    
    return render_template("dashboard_admin.html", 
        total_empleados=total_empleados,
        total_encuestas=total_encuestas,
        total_denuncias=total_denuncias,
        total_capacitaciones=total_capacitaciones,
        role=session.get("role"))

def dashboard_rrhh():
    """Dashboard para Recursos Humanos con indicadores de riesgo."""
    indicadores = database.query_db("""
        SELECT u.nombre_completo, u.departamento, u.puesto,
               i.nivel_estres, i.clima_laboral, i.satisfaccion, i.riesgo_rotacion,
               i.fecha_evaluacion
        FROM indicadores i
        JOIN users u ON i.empleado_id = u.id
        ORDER BY i.fecha_evaluacion DESC LIMIT 50
    """)
    
    # Estadísticas generales
    estres_promedio = database.query_db(
        "SELECT AVG(nivel_estres) AS promedio FROM indicadores", one=True)["promedio"] or 0
    clima_promedio = database.query_db(
        "SELECT AVG(clima_laboral) AS promedio FROM indicadores", one=True)["promedio"] or 0
    rotacion_alto_riesgo = database.query_db(
        "SELECT COUNT(*) AS total FROM indicadores WHERE riesgo_rotacion > 0", one=True)["total"] or 0
    
    encuestas_pendientes = database.query_db(
        "SELECT COUNT(DISTINCT empleado_id) AS total FROM users WHERE id NOT IN (SELECT DISTINCT empleado_id FROM respuestas_encuesta)")
    
    denuncias_pendientes = database.query_db(
        "SELECT COUNT(*) AS total FROM denuncias WHERE estado = 'pendiente'", one=True)["total"]
    
    return render_template("dashboard_rrhh.html",
        indicadores=indicadores,
        estres_promedio=round(estres_promedio, 2),
        clima_promedio=round(clima_promedio, 2),
        rotacion_alto_riesgo=rotacion_alto_riesgo,
        encuestas_pendientes=encuestas_pendientes,
        denuncias_pendientes=denuncias_pendientes,
        role=session.get("role"),
        nombre_completo=session.get("nombre_completo"))

def dashboard_empleado():
    """Dashboard para empleado con sus respuestas y estatus."""
    empleado_id = session["user_id"]
    usuario = database.query_db("SELECT * FROM users WHERE id = ?", (empleado_id,), one=True)
    
    mis_respuestas = database.query_db("""
        SELECT c.nombre, COUNT(*) AS respuestas, MAX(r.fecha_respuesta) AS ultima_respuesta
        FROM respuestas_encuesta r
        JOIN cuestionarios c ON r.cuestionario_id = c.id
        WHERE r.empleado_id = ?
        GROUP BY r.cuestionario_id
    """, (empleado_id,))
    
    mi_indicador = database.query_db(
        "SELECT * FROM indicadores WHERE empleado_id = ? ORDER BY fecha_evaluacion DESC LIMIT 1",
        (empleado_id,), one=True)
    
    mis_capacitaciones = database.query_db("""
        SELECT c.titulo, c.fecha_inicio, c.fecha_fin, ac.asistio, ac.calificacion
        FROM capacitaciones c
        LEFT JOIN asistencia_capacitacion ac ON c.id = ac.capacitacion_id
        WHERE c.id NOT IN (SELECT capacitacion_id FROM asistencia_capacitacion WHERE empleado_id = ?)
           OR ac.empleado_id = ?
        ORDER BY c.fecha_inicio DESC
    """, (empleado_id, empleado_id))
    
    return render_template("dashboard_empleado.html",
        usuario=usuario,
        mis_respuestas=mis_respuestas,
        mi_indicador=mi_indicador,
        mis_capacitaciones=mis_capacitaciones,
        role=session.get("role"),
        nombre_completo=session.get("nombre_completo"))

# ==================== ENCUESTAS Y CUESTIONARIOS ====================

@app.route("/encuestas")
@login_required()
def encuestas():
    """Muestra encuestas disponibles para que el empleado responda."""
    cuestionarios = database.query_db("""
        SELECT c.* FROM cuestionarios c WHERE c.activo = 1
    """)
    
    if session.get("role") == "empleado":
        empleado_id = session["user_id"]
        # Marcar cuestionarios ya respondidos
        for cuest in cuestionarios:
            respondido = database.query_db(
                "SELECT COUNT(*) AS total FROM respuestas_encuesta WHERE empleado_id = ? AND cuestionario_id = ?",
                (empleado_id, cuest["id"]), one=True)["total"]
            cuest["respondido"] = respondido > 0
    
    return render_template("encuestas.html", cuestionarios=cuestionarios, role=session.get("role"))

@app.route("/encuesta/<int:cuestionario_id>", methods=["GET", "POST"])
@login_required()
def responder_encuesta(cuestionario_id):
    """Formulario para responder encuesta."""
    empleado_id = session["user_id"]
    cuestionario = database.query_db(
        "SELECT * FROM cuestionarios WHERE id = ?", (cuestionario_id,), one=True)
    
    if not cuestionario:
        return render_template("error.html", mensaje="Encuesta no encontrada"), 404
    
    if request.method == "POST":
        preguntas = database.query_db(
            "SELECT id FROM preguntas WHERE cuestionario_id = ? ORDER BY orden", (cuestionario_id,))
        
        for pregunta_row in preguntas:
            pregunta_id = pregunta_row["id"]
            respuesta = request.form.get(f"respuesta_{pregunta_id}")
            
            database.query_db("""
                INSERT INTO respuestas_encuesta (empleado_id, cuestionario_id, pregunta_id, respuesta)
                VALUES (?, ?, ?, ?)
            """, (empleado_id, cuestionario_id, pregunta_id, respuesta))
        
        # Calcular indicadores automáticamente
        calcular_indicadores(empleado_id)
        
        return redirect(url_for("encuestas"))
    
    preguntas = database.query_db(
        "SELECT * FROM preguntas WHERE cuestionario_id = ? ORDER BY orden", (cuestionario_id,))
    
    return render_template("encuesta_form.html", cuestionario=cuestionario, preguntas=preguntas)

def calcular_indicadores(empleado_id):
    """Calcula indicadores de estrés, clima laboral y riesgo de rotación."""
    respuestas = database.query_db("""
        SELECT re.respuesta, p.tipo
        FROM respuestas_encuesta re
        JOIN preguntas p ON re.pregunta_id = p.id
        WHERE re.empleado_id = ?
    """, (empleado_id,))
    
    # Lógica simple de cálculo (mejorar según necesidad)
    nivel_estres = sum(1 for r in respuestas if r["respuesta"] in ["si", "alto"]) / max(len(respuestas), 1) * 10
    clima_laboral = 10 - nivel_estres
    riesgo_rotacion = 1 if nivel_estres > 7 else 0
    
    database.query_db("""
        INSERT INTO indicadores (empleado_id, nivel_estres, clima_laboral, satisfaccion, riesgo_rotacion, factores_riesgo)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (empleado_id, nivel_estres, clima_laboral, 10 - nivel_estres, riesgo_rotacion,
          "Estrés laboral elevado" if nivel_estres > 7 else "Normal"))

# ==================== DENUNCIAS CONFIDENCIALES ====================

@app.route("/denuncias", methods=["GET", "POST"])
@login_required()
def denuncias():
    """Plataforma de denuncias confidenciales."""
    if request.method == "POST":
        tipo_denuncia = request.form.get("tipo_denuncia")
        descripcion = request.form.get("descripcion")
        fecha_evento = request.form.get("fecha_evento")
        evidencia = request.form.get("evidencia")
        
        empleado_id = session["user_id"] if session.get("role") == "empleado" else None
        
        database.query_db("""
            INSERT INTO denuncias (empleado_id, tipo_denuncia, descripcion, fecha_evento, evidencia)
            VALUES (?, ?, ?, ?, ?)
        """, (empleado_id, tipo_denuncia, descripcion, fecha_evento, evidencia))
        
        return render_template("denuncia_confirmacion.html",
            mensaje="Denuncia registrada confidencialmente. Se investigará y se notificará del seguimiento.")
    
    return render_template("denuncia_form.html")

@app.route("/gestionar-denuncias")
@login_required(role="recursos_humanos")
def gestionar_denuncias():
    """Panel de RRHH para gestionar denuncias."""
    denuncias_list = database.query_db("""
        SELECT d.*, u.nombre_completo
        FROM denuncias d
        LEFT JOIN users u ON d.empleado_id = u.id
        ORDER BY d.fecha_denuncia DESC
    """)
    
    return render_template("gestionar_denuncias.html", denuncias=denuncias_list, role=session.get("role"))

@app.route("/denuncia/<int:denuncia_id>/resolver", methods=["POST"])
@login_required(role="recursos_humanos")
def resolver_denuncia(denuncia_id):
    """Marca denuncia como resuelta."""
    acciones = request.form.get("acciones_tomadas")
    
    database.query_db("""
        UPDATE denuncias
        SET estado = 'resuelto', fecha_resolucion = CURRENT_TIMESTAMP, acciones_tomadas = ?
        WHERE id = ?
    """, (acciones, denuncia_id))
    
    return redirect(url_for("gestionar_denuncias"))

# ==================== CAPACITACIONES ====================

@app.route("/capacitaciones")
@login_required()
def capacitaciones():
    """Listado de capacitaciones disponibles."""
    capacitaciones_list = database.query_db("""
        SELECT c.*, u.nombre_completo AS responsable
        FROM capacitaciones c
        LEFT JOIN users u ON c.responsable_id = u.id
        WHERE c.fecha_fin >= DATE('now')
        ORDER BY c.fecha_inicio ASC
    """)
    
    if session.get("role") == "empleado":
        empleado_id = session["user_id"]
        for cap in capacitaciones_list:
            asistencia = database.query_db(
                "SELECT asistio FROM asistencia_capacitacion WHERE capacitacion_id = ? AND empleado_id = ?",
                (cap["id"], empleado_id), one=True)
            cap["asistencia"] = asistencia["asistio"] if asistencia else None
    
    return render_template("capacitaciones.html", capacitaciones=capacitaciones_list, role=session.get("role"))

@app.route("/capacitacion/<int:capacitacion_id>/asistencia", methods=["POST"])
@login_required()
def registrar_asistencia(capacitacion_id):
    """Registra asistencia de empleado a capacitación."""
    empleado_id = session["user_id"]
    
    database.query_db("""
        INSERT OR REPLACE INTO asistencia_capacitacion (capacitacion_id, empleado_id, asistio)
        VALUES (?, ?, 1)
    """, (capacitacion_id, empleado_id))
    
    return jsonify({"success": True, "mensaje": "Asistencia registrada"})

# ==================== REPORTES ====================

@app.route("/reportes")
@login_required(role="recursos_humanos")
def reportes():
    """Panel de reportes para RRHH."""
    return render_template("reportes.html", role=session.get("role"))

@app.route("/reporte/indicadores/pdf")
@login_required(role="recursos_humanos")
def reporte_indicadores_pdf():
    """Genera reporte PDF de indicadores de riesgo."""
    indicadores = database.query_db("""
        SELECT u.nombre_completo, u.departamento, u.puesto,
               i.nivel_estres, i.clima_laboral, i.satisfaccion, i.riesgo_rotacion, i.fecha_evaluacion
        FROM indicadores i
        JOIN users u ON i.empleado_id = u.id
        ORDER BY i.nivel_estres DESC
    """)
    
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from io import BytesIO
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    titulo = Paragraph("Reporte de Indicadores de Riesgo Psicosocial NOM-035", styles['Title'])
    fecha = Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
    elements.extend([titulo, fecha, Spacer(1, 0.3*inch)])
    
    # Tabla
    data = [["Empleado", "Departamento", "Estrés", "Clima Laboral", "Satisfacción", "Riesgo Rotación"]]
    for ind in indicadores:
        data.append([
            ind["nombre_completo"],
            ind["departamento"],
            f"{ind['nivel_estres']:.1f}",
            f"{ind['clima_laboral']:.1f}",
            f"{ind['satisfaccion']:.1f}",
            "Alto" if ind["riesgo_rotacion"] else "Bajo"
        ])
    
    tabla = Table(data)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), "#4472C4"),
        ('TEXTCOLOR', (0, 0), (-1, 0), "white"),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, "black")
    ]))
    
    elements.append(tabla)
    doc.build(elements)
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="indicadores_nom035.pdf", mimetype="application/pdf")

@app.route("/reporte/encuestas/excel")
@login_required(role="recursos_humanos")
def reporte_encuestas_excel():
    """Genera reporte Excel de respuestas de encuestas."""
    import openpyxl
    from io import BytesIO
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Respuestas"
    
    # Encabezados
    ws.append(["Empleado", "Cuestionario", "Pregunta", "Respuesta", "Fecha"])
    
    respuestas = database.query_db("""
        SELECT u.nombre_completo, c.nombre, p.pregunta, re.respuesta, re.fecha_respuesta
        FROM respuestas_encuesta re
        JOIN users u ON re.empleado_id = u.id
        JOIN cuestionarios c ON re.cuestionario_id = c.id
        JOIN preguntas p ON re.pregunta_id = p.id
        ORDER BY re.fecha_respuesta DESC
    """)
    
    for resp in respuestas:
        ws.append([
            resp["nombre_completo"],
            resp["nombre"],
            resp["pregunta"],
            resp["respuesta"],
            resp["fecha_respuesta"]
        ])
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name="respuestas_encuestas.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ==================== RUTAS DE ADMINISTRACIÓN ====================

@app.route("/gestion-usuarios")
@login_required(role="admin")
def gestion_usuarios():
    """Gestión de usuarios (admin)."""
    usuarios = database.query_db("SELECT id, username, nombre_completo, role, email, departamento, puesto FROM users")
    return render_template("gestion_usuarios.html", usuarios=usuarios, role=session.get("role"))

@app.route("/usuario/crear", methods=["POST"])
@login_required(role="admin")
def crear_usuario():
    """Crea un nuevo usuario con rol admin, recursos_humanos o empleado."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role")
    nombre_completo = request.form.get("nombre_completo", "").strip()
    email = request.form.get("email", "").strip()
    departamento = request.form.get("departamento", "").strip()
    puesto = request.form.get("puesto", "").strip()

    error = None
    if not username or not password or role not in ("admin", "recursos_humanos", "empleado"):
        error = "Debe completar usuario, contraseña y seleccionar un rol válido."
    else:
        existente = database.query_db("SELECT id FROM users WHERE username = ?", (username,), one=True)
        if existente:
            error = "El nombre de usuario ya existe. Elija otro."

    if error:
        usuarios = database.query_db("SELECT id, username, nombre_completo, role, email, departamento, puesto FROM users")
        return render_template("gestion_usuarios.html", usuarios=usuarios, role=session.get("role"), error=error)

    password_hash = generate_password_hash(password)
    database.query_db(
        "INSERT INTO users (username, password_hash, role, email, nombre_completo, departamento, puesto) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (username, password_hash, role, email, nombre_completo, departamento, puesto)
    )

    usuarios = database.query_db("SELECT id, username, nombre_completo, role, email, departamento, puesto FROM users")
    mensaje = "Usuario creado correctamente."
    return render_template("gestion_usuarios.html", usuarios=usuarios, role=session.get("role"), mensaje=mensaje)

@app.route("/usuario/<int:usuario_id>/editar", methods=["POST"])
@login_required(role="admin")
def editar_usuario(usuario_id):
    """Edita datos de un usuario."""
    nombre_completo = request.form.get("nombre_completo")
    email = request.form.get("email")
    departamento = request.form.get("departamento")
    puesto = request.form.get("puesto")
    role = request.form.get("role")
    
    database.query_db("""
        UPDATE users SET nombre_completo = ?, email = ?, departamento = ?, puesto = ?, role = ?
        WHERE id = ?
    """, (nombre_completo, email, departamento, puesto, role, usuario_id))
    
    return jsonify({"success": True, "mensaje": "Usuario actualizado"})

# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def page_not_found(error):
    return render_template("error.html", mensaje="Página no encontrada"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("error.html", mensaje="Error interno del servidor"), 500

# ==================== INICIALIZACIÓN ====================

if __name__ == "__main__":
    database.init_db()
    host = os.environ.get("IP", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ["1", "true", "yes"]
    app.run(host=host, port=port, debug=debug)

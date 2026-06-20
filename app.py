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
    # Nuevos indicadores para el dashboard principal
    total_centros = database.query_db("SELECT COUNT(*) AS total FROM centros", one=True)["total"]
    total_evaluaciones = database.query_db("SELECT COUNT(*) AS total FROM evaluaciones", one=True)["total"]

    # Distribución por niveles de riesgo (para gráfico)
    niveles = database.query_db("SELECT nivel_riesgo, COUNT(*) AS total FROM evaluaciones GROUP BY nivel_riesgo")

    # Últimas evaluaciones registradas
    recientes = database.query_db("SELECT e.*, c.razon_social FROM evaluaciones e LEFT JOIN centros c ON e.centro_id = c.id ORDER BY e.fecha DESC LIMIT 10")

    return render_template("dashboard_admin.html", 
        total_empleados=total_empleados,
        total_encuestas=total_encuestas,
        total_denuncias=total_denuncias,
        total_capacitaciones=total_capacitaciones,
        total_centros=total_centros,
        total_evaluaciones=total_evaluaciones,
        niveles=niveles,
        recientes=recientes,
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
    
    # Mostrar últimas evaluaciones para el empleado (visibilidad general)
    recientes = database.query_db("SELECT e.*, c.razon_social FROM evaluaciones e LEFT JOIN centros c ON e.centro_id = c.id ORDER BY e.fecha DESC LIMIT 5")

    return render_template("dashboard_empleado.html",
        usuario=usuario,
        mis_respuestas=mis_respuestas,
        mi_indicador=mi_indicador,
        mis_capacitaciones=mis_capacitaciones,
        recientes=recientes,
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


# ==================== GESTIÓN DE CENTROS Y EVALUACIONES (HTML + API) ====================


@app.route('/registrar-centro', methods=['GET', 'POST'])
@login_required(role='admin')
def registrar_centro():
    mensaje = None
    if request.method == 'POST':
        razon_social = request.form.get('razon_social')
        domicilio = request.form.get('domicilio')
        actividad_principal = request.form.get('actividad_principal')
        total_trabajadores = request.form.get('total_trabajadores')
        try:
            total = int(total_trabajadores)
        except Exception:
            total = 0

        database.query_db(
            "INSERT INTO centros (razon_social, domicilio, actividad_principal, total_trabajadores) VALUES (?, ?, ?, ?)",
            (razon_social, domicilio, actividad_principal, total)
        )
        mensaje = 'Centro registrado correctamente.'

    return render_template('registrar_centro.html', mensaje=mensaje, role=session.get('role'))


@app.route('/api/centros', methods=['GET', 'POST'])
def api_centros():
    if request.method == 'GET':
        centros = database.query_db('SELECT * FROM centros')
        return jsonify(centros)

    data = request.get_json() or {}
    razon_social = data.get('razon_social')
    domicilio = data.get('domicilio')
    actividad = data.get('actividad_principal')
    total = int(data.get('total_trabajadores') or 0)
    database.query_db('INSERT INTO centros (razon_social, domicilio, actividad_principal, total_trabajadores) VALUES (?, ?, ?, ?)',
                      (razon_social, domicilio, actividad, total))
    return jsonify({'success': True, 'message': 'Centro creado'})


@app.route('/api/evaluaciones', methods=['GET'])
def api_evaluaciones():
    rows = database.query_db("SELECT e.*, c.razon_social FROM evaluaciones e LEFT JOIN centros c ON e.centro_id = c.id ORDER BY e.id DESC")
    return jsonify(rows)


@app.route('/api/evaluacion', methods=['POST'])
def api_evaluacion():
    data = request.get_json() or {}
    centro_id = data.get('centro_id')
    tipo_guia = data.get('tipo_guia')
    datos = data.get('datos') or {}
    import json as _json
    puntaje = None
    nivel_riesgo = None
    acciones_necesarias = None

    # Intentar cálculo automático según tipo de guía usando el motor nom035_engine
    try:
        from nom035_engine import EvaluadorGuiaII, EvaluacionGuiaI

        if tipo_guia == 'II':
            # Datos esperados: datos['respuestas'] -> dict {item_num: 'Siempre'|...}
            respuestas = datos.get('respuestas') or datos.get('items') or {}
            # Normalize keys to ints and map numeric answers (0-4) to text scale expected
            num_to_text = {4: 'Siempre', 3: 'Casi siempre', 2: 'Algunas veces', 1: 'Casi nunca', 0: 'Nunca'}
            respuestas_usuario = {}
            for k, v in respuestas.items():
                try:
                    ik = int(k)
                except Exception:
                    continue
                # If value is numeric string or int, map to text
                if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit()):
                    try:
                        vv = int(v)
                        respuestas_usuario[ik] = num_to_text.get(vv, 'Nunca')
                    except Exception:
                        respuestas_usuario[ik] = str(v)
                else:
                    respuestas_usuario[ik] = str(v)

            if not respuestas_usuario:
                return jsonify({'success': False, 'message': 'Respuestas inválidas para Guía II'}), 400

            evaluador = EvaluadorGuiaII()
            resultados = evaluador.evaluar_cuestionario(respuestas_usuario)
            puntaje = resultados.get('Calificacion_Final')
            nivel_riesgo = evaluador.obtener_semaforo_final(puntaje)
            acciones_necesarias = evaluador.obtener_acciones_necesarias(nivel_riesgo)

        elif tipo_guia == 'I':
            # Guía I espera listas booleanas por secciones
            s1 = datos.get('respuestas_seccion_1') or datos.get('s1') or []
            s2 = datos.get('respuestas_seccion_2') or datos.get('s2') or []
            s3 = datos.get('respuestas_seccion_3') or datos.get('s3') or []
            s4 = datos.get('respuestas_seccion_4') or datos.get('s4') or []
            # Normalizar a booleanos
            def to_bool_list(l):
                return [bool(x) for x in l]

            if any([s1, s2, s3, s4]):
                ev = EvaluacionGuiaI(to_bool_list(s1), to_bool_list(s2), to_bool_list(s3), to_bool_list(s4))
                requiere, mensaje = ev.requiere_valoracion_clinica()
                nivel_riesgo = 'Requiere valoración clínica' if requiere else 'No requiere valoración'
                puntaje = None
                acciones_necesarias = mensaje
    except Exception:
        # Si ocurre cualquier error con el motor, guardar sin cálculo automático
        puntaje = None
        nivel_riesgo = None
        acciones_necesarias = None

    database.query_db(
        "INSERT INTO evaluaciones (centro_id, tipo_guia, datos_json, puntaje, nivel_riesgo, acciones_necesarias, fecha) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (centro_id, tipo_guia, _json.dumps(datos, ensure_ascii=False), puntaje, nivel_riesgo, acciones_necesarias, datetime.now().strftime('%Y-%m-%d'))
    )
    resp = {'success': True, 'message': 'Evaluación registrada', 'puntaje': puntaje, 'nivel_riesgo': nivel_riesgo}
    if acciones_necesarias:
        resp['acciones_necesarias'] = acciones_necesarias
    return jsonify(resp)


@app.route('/reporte_excel')
@login_required(role='admin')
def reporte_excel():
    """Exporta todas las evaluaciones a Excel (enlazada desde dashboard)."""
    evaluaciones = database.query_db("SELECT e.*, c.razon_social FROM evaluaciones e LEFT JOIN centros c ON e.centro_id = c.id ORDER BY e.fecha DESC")
    buffer = crear_excel_resumen(evaluaciones)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='evaluaciones_nom035.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/evaluacion/<int:evaluacion_id>/pdf')
@login_required()
def evaluacion_pdf(evaluacion_id):
    """Genera y descarga el PDF de una evaluación específica."""
    row = database.query_db("SELECT e.*, c.razon_social, c.domicilio, c.actividad_principal, c.total_trabajadores FROM evaluaciones e LEFT JOIN centros c ON e.centro_id = c.id WHERE e.id = ?", (evaluacion_id,), one=True)
    if not row:
        return render_template('error.html', mensaje='Evaluación no encontrada'), 404

    centro = {
        'razon_social': row.get('razon_social'),
        'domicilio': row.get('domicilio'),
        'actividad_principal': row.get('actividad_principal'),
        'total_trabajadores': row.get('total_trabajadores')
    }

    buffer = crear_pdf_evaluacion(row, centro)
    return send_file(buffer, as_attachment=True, download_name=f"evaluacion_{evaluacion_id}.pdf", mimetype='application/pdf')

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

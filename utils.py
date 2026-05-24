import json  # Para serializar y deserializar datos de evaluación.
from io import BytesIO  # Para generar archivos en memoria.
from datetime import datetime  # Para fechas de reporte.
from reportlab.lib.pagesizes import letter  # Tamaño de página para PDF.
from reportlab.lib.units import inch  # Unidad de medida para PDF.
from reportlab.pdfgen import canvas  # Herramienta para dibujar en PDF.
from openpyxl import Workbook  # Para crear archivos Excel.


def crear_pdf_evaluacion(evaluacion, centro):
    """Genera un PDF con el detalle de una evaluación NOM-035."""
    buffer = BytesIO()  # Crea buffer en memoria para guardar el PDF.
    documento = canvas.Canvas(buffer, pagesize=letter)  # Crea lienzo PDF.

    titulo = f"Reporte La Gacela NOM-035 - Evaluación #{evaluacion['id']}"  # Título del PDF.
    documento.setTitle(titulo)  # Establece metadatos de título.

    documento.setFont("Helvetica-Bold", 16)  # Fuente para el título.
    documento.drawString(1 * inch, 10.5 * inch, titulo)  # Dibuja el título.

    documento.setFont("Helvetica", 11)  # Fuente normal para texto.
    documento.drawString(1 * inch, 10.0 * inch, f"Empresa: {centro['razon_social']}")
    documento.drawString(1 * inch, 9.7 * inch, f"Domicilio: {centro['domicilio']}")
    documento.drawString(1 * inch, 9.4 * inch, f"Actividad: {centro['actividad_principal']}")
    documento.drawString(1 * inch, 9.1 * inch, f"Total trabajadores: {centro['total_trabajadores']}")
    documento.drawString(1 * inch, 8.8 * inch, f"Tipo de guía: {evaluacion['tipo_guia']}")
    documento.drawString(1 * inch, 8.5 * inch, f"Fecha de evaluación: {evaluacion['fecha']}")
    documento.drawString(1 * inch, 8.2 * inch, f"Nivel de riesgo: {evaluacion['nivel_riesgo']}")

    documento.drawString(1 * inch, 7.8 * inch, "Detalle de datos de evaluación:")

    datos = json.loads(evaluacion['datos_json'])  # Convierte JSON a dict.
    y_position = 7.4 * inch  # Posición vertical para empezar el detalle.

    for campo, valor in datos.items():
        documento.drawString(1.1 * inch, y_position, f"{campo}: {valor}")  # Dibuja cada campo.
        y_position -= 0.25 * inch  # Baja línea para siguiente valor.
        if y_position < 1 * inch:  # Si llega al final de la página,
            documento.showPage()  # agrega nueva página
            documento.setFont("Helvetica", 11)  # vuelve a establecer fuente
            y_position = 10.5 * inch  # reinicia la posición vertical.

    documento.showPage()  # Finaliza la página actual.
    documento.save()  # Guarda el contenido en el buffer.

    buffer.seek(0)  # Retrocede al inicio del archivo.
    return buffer  # Retorna el PDF en memoria.


def crear_excel_resumen(evaluaciones):
    """Genera un archivo Excel con el listado de evaluaciones guardadas."""
    libro = Workbook()  # Crea nuevo libro de Excel.
    hoja = libro.active  # Selecciona la hoja activa.
    hoja.title = "Evaluaciones"  # Asigna nombre a la hoja.

    # Encabezados de columna.
    hoja.append([
        "ID",
        "Centro de Trabajo",
        "Tipo de Guía",
        "Puntaje",
        "Nivel de Riesgo",
        "Fecha"
    ])

    for eval_item in evaluaciones:
        datos = json.loads(eval_item['datos_json'])  # Extrae datos JSON.
        hoja.append([
            eval_item['id'],
            eval_item['razon_social'],
            eval_item['tipo_guia'],
            eval_item['puntaje'] or "N/A",
            eval_item['nivel_riesgo'] or "N/A",
            eval_item['fecha']
        ])

    buffer = BytesIO()  # Buffer en memoria para el archivo Excel.
    libro.save(buffer)  # Guarda el libro en memoria.
    buffer.seek(0)  # Regresa al inicio del buffer.
    return buffer  # Devuelve el archivo Excel.

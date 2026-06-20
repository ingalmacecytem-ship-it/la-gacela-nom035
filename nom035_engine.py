import json

class CentroDeTrabajo:
    """Representa los datos generales del centro de trabajo evaluado (Num. 7.7)"""
    def __init__(self, razon_social, domicilio, actividad_principal, total_trabajadores):
        self.razon_social = razon_social
        self.domicilio = domicilio
        self.actividad_principal = actividad_principal
        self.total_trabajadores = total_trabajadores

    def obtener_guia_correspondiente(self):
        """Determina automáticamente qué guía de referencia aplicar por tamaño de centro de trabajo"""
        if self.total_trabajadores <= 15:
            return "Solo aplica Guía de Referencia I (Eventos Traumáticos) y Políticas."
        elif 16 <= self.total_trabajadores <= 50:
            return "Aplica Guía de Referencia II (Factores de Riesgo Psicosocial)."
        else:
            return "Aplica Guía de Referencia III (Factores de Riesgo e Entorno Organizacional)."


class EvaluacionGuiaI:
    """Implementa la Guía de Referencia I: Acontecimientos Traumáticos Severos"""
    def __init__(self, respuestas_seccion_1, respuestas_seccion_2, respuestas_seccion_3, respuestas_seccion_4):
        # Listas de booleanos (True = SI, False = NO)
        self.s1 = respuestas_seccion_1  # 6 preguntas (Acontecimiento)
        self.s2 = respuestas_seccion_2  # 2 preguntas (Recuerdos persistentes)
        self.s3 = respuestas_seccion_3  # 7 preguntas (Esfuerzo por evitar)
        self.s4 = respuestas_seccion_4  # 5 preguntas (Afectación)

    def requiere_valoracion_clinica(self):
        """Algoritmo oficial dictado por la Guía de Referencia I"""
        # Si todas las respuestas de la Sección I son NO, no requiere valoración
        if not any(self.s1):
            return False, "El trabajador no requiere valoración clínica."
        
        # Si hay algún SI en la Sección I, se evalúan los criterios de las secciones II, III y IV
        criterio_ii = any(self.s2)                         # Al menos un SI
        criterio_iii = sum(1 for r in self.s3 if r) >= 3   # 3 o más SI
        criterio_iv = sum(1 for r in self.s4 if r) >= 2    # 2 o más SI

        if criterio_ii or criterio_iii or criterio_iv:
            return True, "¡ATENCIÓN! El trabajador requiere valoración clínica (Canalizar a Institución Médica)."
        
        return False, "El trabajador fue expuesto a un evento pero no manifiesta síntomas severos actuales."


class EvaluadorGuiaII:
    """Implementa el Cuestionario de la Guía de Referencia II (Centros de hasta 50 trabajadores)"""
    def __init__(self):
        # Mapeo oficial de ítems inverso (Puntajes: Siempre=0, Casi Siempre=1, Algunas Veces=2, Casi Nunca=3, Nunca=4)
        self.items_inversos = {18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33}
        
        # Agrupamiento oficial por Dominios (Tabla 3)
        self.dominios_items = {
            "Condiciones en el ambiente de trabajo": [1, 2, 3],
            "Carga de trabajo": [4, 5, 6, 7, 8, 9, 41, 42, 43, 10, 11, 12, 13],
            "Falta de control sobre el trabajo": [18, 19, 20, 21, 22, 26, 27],
            "Jornada de trabajo": [14, 15],
            "Interferencia en la relación trabajo-familia": [16, 17],
            "Liderazgo": [23, 24, 25, 28, 29],
            "Relaciones en el trabajo": [30, 31, 32, 44, 45, 46],
            "Violencia": [33, 34, 35, 36, 37, 38, 39, 40]
        }
        
        # Agrupamiento oficial por Categorías (Tabla 3)
        self.categorias_items = {
            "Ambiente de trabajo": [1, 2, 3],
            "Factores propios de la actividad": [4, 5, 6, 7, 8, 9, 41, 42, 43, 10, 11, 12, 13, 18, 19, 20, 21, 22, 26, 27],
            "Organización del tiempo de trabajo": [14, 15, 16, 17],
            "Liderazgo y relaciones en el trabajo": [23, 24, 25, 28, 29, 30, 31, 32, 44, 45, 46, 33, 34, 35, 36, 37, 38, 39, 40]
        }

    def calcular_puntaje_item(self, numero_item, respuesta_texto):
        """Convierte las respuestas de texto en la escala numérica oficial (0 a 4)"""
        escala_normal = {"Siempre": 4, "Casi siempre": 3, "Algunas veces": 2, "Casi nunca": 1, "Nunca": 0}
        escala_inversa = {"Siempre": 0, "Casi siempre": 1, "Algunas veces": 2, "Casi nunca": 3, "Nunca": 4}
        
        opciones = escala_inversa if numero_item in self.items_inversos else escala_normal
        return opciones.get(respuesta_texto, 0)

    def evaluar_cuestionario(self, respuestas_usuario):
        """
        respuestas_usuario: dict -> { 1: "Siempre", 2: "Nunca", ... }
        Devuelve las sumatorias completas de la evaluación.
        """
        puntajes_calculados = {}
        for item, resp in respuestas_usuario.items():
            puntajes_calculados[item] = self.calcular_puntaje_item(item, resp)
            
        # 1. Calificación Final
        calificacion_final = sum(puntajes_calculados.values())
        
        # 2. Calificación de Dominios
        calificaciones_dominios = {}
        for dominio, items in self.dominios_items.items():
            calificaciones_dominios[dominio] = sum(puntajes_calculados.get(i, 0) for i in items)
            
        # 3. Calificación de Categorías
        calificaciones_categorias = {}
        for categoria, items in self.categorias_items.items():
            calificaciones_categorias[categoria] = sum(puntajes_calculados.get(i, 0) for i in items)
            
        return {
            "Calificacion_Final": calificacion_final,
            "Dominios": calificaciones_dominios,
            "Categorias": calificaciones_categorias
        }

    def obtener_semaforo_final(self, puntaje):
        """Rangos oficiales de la calificación final para Guía II"""
        if puntaje < 20:   return "Nulo o despreciable"
        if puntaje < 45:   return "Bajo"
        if puntaje < 70:   return "Medio"
        if puntaje < 90:   return "Alto"
        return "Muy alto"

    def obtener_acciones_necesarias(self, nivel_riesgo):
        """Acciones oficiales dictadas según la Tabla 4 de Niveles de Riesgo"""
        acciones = {
            "Nulo o despreciable": "El riesgo resulta despreciable. No se requieren medidas adicionales.",
            "Bajo": "Es necesario mayor difusión de la política de prevención de riesgos psicosociales y programas preventivos.",
            "Medio": "Se requiere revisar la política de prevención y programas de control. Reforzar su aplicación y difusión mediante un Programa de Intervención.",
            "Alto": "Se requiere análisis detallado por categoría/dominio. Implementar un Programa de Intervención, campañas de sensibilización y revisar políticas.",
            "Muy alto": "¡CRÍTICO! Se requiere análisis profundo urgente, evaluaciones específicas (clínicas/cualitativas), modificar la política preventiva y reforzar programas de control de forma inmediata."
        }
        return acciones.get(nivel_riesgo, "")


# ==========================================
# TEST INTEGRAL DE EJECUCIÓN (SIMULACIÓN)
# ==========================================
if __name__ == "__main__":
    print("--- INICIANDO DIAGNÓSTICO BAJO LA NOM-035-STPS-2018 ---\n")
    
    # 1. Registro del Centro de Trabajo
    mi_empresa = CentroDeTrabajo(
        razon_social="Tecnologías Globales S.A. de C.V.",
        domicilio="Av. de las Ciencias #450, CDMX",
        actividad_principal="Desarrollo de Software y Soporte Técnico",
        total_trabajadores=35
    )
    
    print(f"Empresa: {mi_empresa.razon_social}")
    print(f"Alcance Normativo: {mi_empresa.obtener_guia_correspondiente()}\n")

    # 2. Prueba Guía I (Trabajador con Acontecimiento Traumático Severo)
    # El empleado sufrió un asalto en el trabajo y tiene problemas persistentes para dormir
    respuestas_seccion_1 = [False, True, False, False, False, False] # Pregunta 2: Asaltos = SI
    respuestas_seccion_2 = [True, False]                             # Recuerdos persistentes = SI
    respuestas_seccion_3 = [False, False, False, False, False, False, False]
    respuestas_seccion_4 = [True, False, False, False, False]        # Dificultad para dormir = SI
    
    evaluacion_guia_i = EvaluacionGuiaI(respuestas_seccion_1, respuestas_seccion_2, respuestas_seccion_3, respuestas_seccion_4)
    requiere_ayuda, mensaje_guia_i = evaluacion_guia_i.requiere_valoracion_clinica()
    
    print("=== RESULTADO GUÍA DE REFERENCIA I ===")
    print(f"Dictamen: {mensaje_guia_i}\n")

    # 3. Prueba Guía II (Factores de Riesgo Psicosocial)
    # Simulación de un cuestionario de un trabajador estresado (46 reactivos oficiales)
    respuestas_simuladas = {
        1: "Siempre", 2: "Casi siempre", 3: "Algunas veces", 4: "Siempre", 5: "Siempre",
        6: "Siempre", 7: "Siempre", 8: "Casi siempre", 9: "Siempre", 10: "Algunas veces",
        11: "Siempre", 12: "Casi siempre", 13: "Siempre", 14: "Siempre", 15: "Casi siempre",
        16: "Siempre", 17: "Algunas veces", 
        # Ítems inversos (aquí un estresado contestará "Nunca" o "Casi nunca")
        18: "Nunca", 19: "Nunca", 20: "Casi nunca", 21: "Nunca", 22: "Nunca", 
        23: "Casi nunca", 24: "Nunca", 25: "Nunca", 26: "Casi nunca", 27: "Nunca", 
        28: "Nunca", 29: "Casi nunca", 30: "Nunca", 31: "Nunca", 32: "Casi nunca", 33: "Nunca",
        # Siguen normales
        34: "Siempre", 35: "Siempre", 36: "Casi siempre", 37: "Siempre", 38: "Siempre", 
        39: "Siempre", 40: "Algunas veces", 41: "Siempre", 42: "Siempre", 43: "Casi siempre",
        44: "Siempre", 45: "Siempre", 46: "Casi siempre"
    }

    evaluador_g2 = EvaluadorGuiaII()
    resultados = evaluador_g2.evaluar_cuestionario(respuestas_simuladas)
    
    puntaje_final = resultados["Calificacion_Final"]
    semaforo = evaluador_g2.obtener_semaforo_final(puntaje_final)
    
    print("=== RESULTADO CUESTIONARIO GUÍA DE REFERENCIA II ===")
    print(f"Puntaje Total Obtenido: {puntaje_final} Puntos")
    print(f"Nivel de Riesgo Global: {semaforo.upper()}")
    print(f"Acción Legal Requerida: {evaluador_g2.obtener_acciones_necesarias(semaforo)}\n")
    
    print("--- DESGLOSE POR CATEGORÍAS ---")
    print(json.dumps(resultados["Categorias"], indent=4, ensure_ascii=False))
    print("\n--- DESGLOSE POR DOMINIOS ---")
    print(json.dumps(resultados["Dominios"], indent=4, ensure_ascii=False))
# Manual de Usuario - Manufacturera de Ropa La Gacela

## 1. Introducción

Esta guía explica cómo utilizar la aplicación de evaluación NOM-035 para La Gacela.

## 2. Acceso a la aplicación

1. Abra su navegador.
2. Ingrese a: `http://127.0.0.1:5000`
3. Inicie sesión con las credenciales iniciales:
   - Usuario: `admin`
   - Contraseña: `admin123`

> Se recomienda cambiar la contraseña del administrador después del primer ingreso.

## 3. Página principal

Después de iniciar sesión, verá el `Dashboard La Gacela` con:

- Total de centros registrados.
- Total de evaluaciones realizadas.
- Distribución de niveles de riesgo.

## 4. Registrar un centro de trabajo

1. Haga clic en `Registrar Centro` en el menú.
2. Complete los campos:
   - Razón social.
   - Domicilio.
   - Actividad principal.
   - Total de trabajadores.
3. Pulse `Registrar centro`.
4. Verá un mensaje de confirmación si el centro se guardó correctamente.

## 5. Registrar una evaluación NOM-035

1. Haga clic en `Evaluación` en el menú.
2. Seleccione un centro de trabajo.
3. Elija el tipo de guía:
   - `II` para Factores de riesgo psicosocial.
   - `I` para Acontecimiento traumático.
4. Ingrese valores de 0 a 4 para cada ítem del cuestionario.
5. Añada comentarios adicionales si lo desea.
6. Pulse `Guardar evaluación`.
7. La aplicación calcula el nivel de riesgo y guarda la evaluación.

## 6. Generar reportes

### PDF individual

1. En el dashboard o en el panel de evaluaciones, use el enlace de reporte PDF.
2. Se generará un archivo `reporte_la_gacela_<id>.pdf` con los detalles de la evaluación.

### Exportar a Excel

1. Solo usuario administrador puede descargar el reporte Excel.
2. Haga clic en `Descargar Excel` desde el dashboard.
3. El archivo se descargará como `evaluaciones_la_gacela.xlsx`.

## 7. Uso del frontend web/PWA

1. Abra: `http://127.0.0.1:5000/app`
2. Inicie sesión con el mismo usuario y contraseña.
3. Use esta interfaz para:
   - iniciar sesión,
   - registrar centros,
   - registrar evaluaciones,
   - consultar historial.

## 8. Uso de la app móvil de demostración

1. Abra la carpeta `mobile_app`.
2. Siga las instrucciones de `mobile_app/README.md`.
3. Ajuste la variable `BACKEND_URL` en `App.js` al servidor donde corre el backend.

## 9. Buenas prácticas

- Use siempre un navegador moderno.
- Cambie la contraseña del administrador en cuanto sea posible.
- Mantenga respaldos periódicos del archivo de base de datos.
- Use el modo `hosting` cuando despliegue en un servidor de producción.

## 10. Soporte

Para consultas técnicas, revise `MANUAL_TECNICO.md` o contacte con el equipo de TI de La Gacela.

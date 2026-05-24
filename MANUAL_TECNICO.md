# Manual Técnico - Manufacturera de Ropa La Gacela

## 1. Descripción del proyecto

Esta aplicación gestiona la evaluación de riesgos psicosociales bajo la norma NOM-035 STPS para Manufacturera de Ropa La Gacela. Incluye:

- Backend en Python y Flask.
- Base de datos SQLite (`la_gacela_nom035.db`).
- Frontend web responsive y PWA en `web_app/`.
- App móvil de demostración con Expo en `mobile_app/`.
- Reportes PDF y exportación Excel.

## 2. Estructura de archivos

- `app.py` - servidor Flask principal.
- `database.py` - inicialización y consultas SQLite.
- `utils.py` - generación de PDF y Excel.
- `wsgi.py` - punto de entrada WSGI para hosting.
- `deploy.ps1` - script de despliegue local y para hosting.
- `templates/` - vistas HTML para la app web tradicional.
- `static/css/style.css` - estilos para la app web.
- `web_app/` - frontend PWA.
- `mobile_app/` - aplicación móvil de demostración Expo.
- `requirements.txt` - dependencias Python.
- `README.md` - guía de uso general.

## 3. Dependencias

Dependencias Python:

- Flask
- openpyxl
- reportlab

Para ejecutar en hosting se recomienda instalar también:

- waitress

## 4. Preparación del entorno

Desde la raíz del proyecto:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 5. Inicialización de la base de datos

La inicialización se realiza automáticamente al ejecutar `deploy.ps1` o `app.py`:

```powershell
python app.py
```

También puede ejecutarse manualmente:

```powershell
venv\Scripts\python.exe -c "import database; database.init_db()"
```

## 6. Ejecución local

Para iniciar localmente:

```powershell
.
\deploy.ps1 -Mode local
```

Esto:

- crea el entorno virtual si no existe
- instala dependencias
- inicializa la base de datos
- inicia el servidor Flask en `http://127.0.0.1:5000`

## 7. Despliegue a hosting compatible

Para preparar el paquete de despliegue:

```powershell
.
\deploy.ps1 -Mode hosting
```

Esto generará `deploy_package.zip` listo para subir a su proveedor.

### Subida automática con SCP

Si dispone de `scp`, puede ejecutar:

```powershell
.
\deploy.ps1 -Mode hosting -RemoteHost "mi-servidor.com" -RemoteUser "usuario" -RemotePath "/var/www/la_gacela"
```

### Hosting compatible

El proyecto puede ejecutarse en hosting compatible con WSGI usando `wsgi.py`.
Ejemplo con Waitress:

```powershell
venv\Scripts\python.exe -m pip install waitress
venv\Scripts\python.exe -m waitress --listen=*:8000 wsgi:app
```

## 8. API REST

### Login móvil

- `POST /api/login`
- Body JSON:
  - `username`
  - `password`

### Registrar centros

- `GET /api/centros`
- `POST /api/centros`
- Body JSON:
  - `razon_social`
  - `domicilio`
  - `actividad_principal`
  - `total_trabajadores`

### Evaluaciones

- `POST /api/evaluacion`
- Body JSON:
  - `centro_id`
  - `tipo_guia`
  - `datos` (diccionario adicional)

- `GET /api/evaluaciones`

### Reportes

- `GET /api/reporte/pdf/<id>`
- `GET /api/reporte/excel`

## 9. Consideraciones de mantenimiento

- El archivo de base de datos SQLite es `la_gacela_nom035.db`.
- Hacer copias de seguridad periódicas de datos y reportes.
- Para producción, usar un servidor WSGI y configurar HTTPS.

## 10. Notas de seguridad

- Cambiar la contraseña del usuario `admin` después del primer ingreso.
- Proteger el `SECRET_KEY` de Flask en variables de entorno para producción.
- No exponer archivos `*.db` públicamente.

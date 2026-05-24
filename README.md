# NOM-035 App Web y Móvil - Manufacturera de Ropa La Gacela

Aplicación personalizada para Manufacturera de Ropa La Gacela bajo la norma NOM-035 STPS con backend en Flask, base de datos SQLite, roles de usuario, generación de reportes PDF, exportación a Excel y dashboard.

## Estructura

- `app.py`: servidor Flask principal con rutas web y API.
- `database.py`: inicialización de base de datos y funciones de acceso.
- `utils.py`: generación de PDF y Excel.
- `templates/`: vistas HTML responsive con Bootstrap.
- `static/css/style.css`: estilos adicionales.
- `web_app/`: frontend web/PWA con API REST.
- `mobile_app/`: aplicación móvil de demostración basada en Expo.
- `requirements.txt`: dependencias.
- `la_gacela_nom035.db`: base de datos SQLite personalizada para La Gacela.

## Uso

1. Crear el entorno virtual e instalar dependencias:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Ejecutar el servidor:

```powershell
python app.py
```

3. Abrir en el navegador:

```text
http://127.0.0.1:5000
```

4. Abrir el frontend web/PWA:

```text
http://127.0.0.1:5000/app
```

## Credenciales iniciales

- Usuario: `admin`
- Contraseña: `admin123`

## Características

- Roles: `admin`, `evaluador`, `inspector`
- Dashboard con métricas
- Registro de centros de trabajo
- Evaluación de riesgo NOM-035
- Reportes PDF y Excel
- API REST para integración móvil
- Frontend web PWA instalable en móviles modernos

## Aplicación móvil

Para probar la app móvil de demostración basada en Expo:

```powershell
cd mobile_app
npm install
npm run start
```

Ajusta `BACKEND_URL` en `mobile_app/App.js` al host donde corre el backend.

## Replit

Para ejecutar el proyecto en Replit, importa el repositorio y usa la entrada principal `run_replit.py`.

1. Asegúrate de que el proyecto incluya `run_replit.py`, `.replit` y `replit.nix`.
2. Replit instalará las dependencias desde `requirements.txt`.
3. La app se iniciará automáticamente en el puerto configurado por Replit.

## Despliegue

Use el script de despliegue para preparar el entorno, inicializar la base de datos y ejecutar localmente o empaquetar la aplicación para hosting.

### Ejecución local

```powershell
.
\deploy.ps1 -Mode local
```

### Preparar paquete para hosting

```powershell
.
\deploy.ps1 -Mode hosting
```

### Subida automática con SCP (opcional)

```powershell
.
\deploy.ps1 -Mode hosting -RemoteHost "mi-servidor.com" -RemoteUser "usuario" -RemotePath "/var/www/la_gacela"
```

## Manuales

- `MANUAL_TECNICO.md`: documentación técnica para instalación, despliegue y API.
- `MANUAL_USUARIO.md`: guía de uso para los usuarios de la aplicación.

## Repositorio

El código fuente de este proyecto está publicado en GitHub en:

https://github.com/ingalmacecito-env%C3%ADo-eso/la-gacela-nom035

Puedes añadir estos badges en la documentación del repositorio si lo deseas:

- Estado del repositorio: ![GitHub Repo stars](https://img.shields.io/github/stars/ingalmacecito-env%C3%ADo-eso/la-gacela-nom035)
- Último commit: ![GitHub last commit](https://img.shields.io/github/last-commit/ingalmacecito-env%C3%ADo-eso/la-gacela-nom035)

## Cómo subir los cambios (comandos listos)

Ejecuta estos comandos en la raíz del proyecto para commitear y enviar los cambios al repositorio remoto:

```powershell
cd C:\Users\siste\nom035_app
git add README.md
git commit -m "Add repository link and badges to README"
git push origin main
```

Si aún no has configurado la rama `main` o el remoto `origin`, usa este conjunto de comandos:

```powershell
cd C:\Users\siste\nom035_app
git init
git branch -M main
git remote add origin "https://github.com/ingalmacecito-env%C3%ADo-eso/la-gacela-nom035.git"
git add .
git commit -m "Initial commit - La Gacela NOM-035"
git push -u origin main
```

Si tu GitHub requiere autenticación por token, sigue las instrucciones anteriores para usar `GITHUB_TOKEN` o `gh`.

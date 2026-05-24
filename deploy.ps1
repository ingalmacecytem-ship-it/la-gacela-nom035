param(
    [ValidateSet("local", "hosting")]
    [string]$Mode = "local",
    [string]$RemoteHost = "",
    [string]$RemoteUser = "",
    [string]$RemotePath = ""
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "[DEPLOY] Proyecto raíz: $projectRoot"
Write-Host "[DEPLOY] Modo: $Mode"

# Crea y configura el entorno virtual si no existe.
if (-Not (Test-Path "$projectRoot\venv")) {
    Write-Host "[DEPLOY] Creando entorno virtual..."
    python -m venv venv
}

$pythonPath = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-Not (Test-Path $pythonPath)) {
    Write-Error "No se encontró el intérprete de Python en $pythonPath. Verifica que el entorno virtual se haya creado correctamente."
    exit 1
}

Write-Host "[DEPLOY] Instalando dependencias..."
& $pythonPath -m pip install --upgrade pip
& $pythonPath -m pip install -r requirements.txt

Write-Host "[DEPLOY] Inicializando base de datos..."
& $pythonPath -c "import database; database.init_db()"

if ($Mode -eq "local") {
    Write-Host "[DEPLOY] Ejecutando servidor local en http://127.0.0.1:5000 ..."
    & $pythonPath app.py
    return
}

if ($Mode -eq "hosting") {
    $packageName = "deploy_package.zip"
    if (Test-Path $packageName) {
        Remove-Item $packageName -Force
    }

    Write-Host "[DEPLOY] Empaquetando aplicación para hosting..."
    Compress-Archive -Path "*" -DestinationPath $packageName -Force -Exclude "venv","*.pyc","__pycache__","*.db","deploy_package.zip"

    if (-Not [string]::IsNullOrEmpty($RemoteHost) -and -Not [string]::IsNullOrEmpty($RemoteUser) -and -Not [string]::IsNullOrEmpty($RemotePath)) {
        Write-Host "[DEPLOY] Subiendo paquete a $RemoteUser@$RemoteHost:$RemotePath ..."
        if (Get-Command scp -ErrorAction SilentlyContinue) {
            scp $packageName "$RemoteUser@$RemoteHost:$RemotePath"
            Write-Host "[DEPLOY] Paquete subido correctamente."
        } else {
            Write-Warning "scp no está disponible en este sistema. Copia manualmente deploy_package.zip a su hosting." 
        }
    } else {
        Write-Host "[DEPLOY] Paquete preparado: $packageName"
        Write-Host "[DEPLOY] Si deseas subirlo a un servidor remoto, proporciona RemoteHost, RemoteUser y RemotePath." 
    }
}

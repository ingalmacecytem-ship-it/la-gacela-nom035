<#
publish_github.ps1
Automatiza la creación de un repositorio en GitHub y sube el proyecto.
Requisitos:
- Git instalado y en PATH
- (Recomendado) GitHub CLI (`gh`) configurado con `gh auth login`
- Alternativa: exportar una variable de entorno `GITHUB_TOKEN` con un PAT con scope `repo`.

Uso:
- Ejecutar desde la raíz del proyecto:
    .\publish_github.ps1 -RepoName "la-gacela-nom035" -Description "Repo NOM-035 La Gacela"
- Si usas `gh`, el script creará y empujará automáticamente.
- Si usas `GITHUB_TOKEN`, el script usará la API de GitHub para crear el repo.
#>

param(
    [string]$RepoName = "la-gacela-nom035",
    [string]$Description = "Repositorio de la aplicación NOM-035 para Manufacturera de Ropa La Gacela",
    [switch]$Private
)

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Err($m){ Write-Host "[ERROR] $m" -ForegroundColor Red }

# Check git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Err "Git no está instalado o no está en PATH. Instala Git antes de continuar."
    exit 1
}

# Initialize repo if needed
if (-not (Test-Path ".git")) {
    Write-Info "Inicializando repositorio git local..."
    git init
    git branch -M main
}

# Stage and commit
Write-Info "Añadiendo archivos al índice..."
git add .

# Only commit if there are staged changes
$changes = git diff --cached --name-only
if (-not $changes) {
    Write-Info "No hay cambios nuevos para commitear."
} else {
    Write-Info "Creando commit inicial..."
    git commit -m "Publicar proyecto La Gacela NOM-035"
}

# Prefer gh CLI if available
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Info "GitHub CLI detectada. Intentando crear el repo con 'gh'..."
    $flags = "--public"
    if ($Private) { $flags = "--private" }

    # Create repo and push
    gh repo create $RepoName $flags --description "$Description" --source . --remote origin --push

    if ($LASTEXITCODE -eq 0) {
        Write-Info "Repositorio creado y código empujado correctamente."
        gh repo view --web $RepoName
        exit 0
    } else {
        Write-Err "'gh' devolvió un error. Revisa la salida anterior."
        exit 1
    }
}

function Set-GitRemoteOrigin($url) {
    $remoteExists = git remote | Select-String -Pattern '^origin$' -Quiet
    if ($remoteExists) {
        Write-Info "El remoto 'origin' ya existe. Actualizando su URL..."
        git remote set-url origin $url
    } else {
        Write-Info "Agregando remoto origin..."
        git remote add origin $url
    }
}

# If no gh, try using GITHUB_TOKEN
if ($env:GITHUB_TOKEN) {
    Write-Info "GITHUB_TOKEN detectado. Creando repo vía API..."

    $apiUrl = "https://api.github.com/user/repos"
    $body = @{ name = $RepoName; description = $Description; private = $Private.IsPresent } | ConvertTo-Json

    $headers = @{ Authorization = "token $($env:GITHUB_TOKEN)"; "User-Agent" = "publish_github_script" }

    $resp = Invoke-RestMethod -Uri $apiUrl -Method Post -Headers $headers -Body $body -ErrorAction SilentlyContinue

    if ($resp -and $resp.clone_url) {
        Write-Info "Repositorio creado: $($resp.html_url)"
        Set-GitRemoteOrigin $resp.clone_url
        git push -u origin main
        exit 0
    } else {
        Write-Err "Fallo al crear el repo vía API. Revisa que GITHUB_TOKEN sea válido y tenga scope 'repo'."
        exit 1
    }
}

# If neither gh nor token, print manual steps
Write-Info "Ni 'gh' ni 'GITHUB_TOKEN' disponibles. Proporciono pasos manuales para crear y subir el repo."
Write-Host "1) Crea un repositorio en https://github.com/new con el nombre: $RepoName"
Write-Host "2) En la raíz del proyecto ejecuta:
    git remote add origin https://github.com/<TU_USUARIO>/$RepoName.git
    git push -u origin main"

exit 0

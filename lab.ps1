# ===========================================================================
# secure-web-lab - lanzador del laboratorio (Clase 01, por fases)
#
#   Windows PowerShell:   .\lab.ps1 <comando>
#   Linux/macOS/WSL:      ./lab.sh  <comando>   (mismos comandos)
#
# Si Windows bloquea la ejecucion de scripts, en esta misma ventana:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
# ===========================================================================
param([string]$Comando = "ayuda")

# Comprobamos los códigos de salida a mano, para poder dar mensajes claros.
# En PowerShell 7.4+ un comando nativo con exit != 0 lanzaría excepción; lo evitamos.
$ErrorActionPreference = "Continue"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}
Set-Location -Path $PSScriptRoot

# El esquema de red usa caracteres de dibujo: sin UTF-8 sale como basura.
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# Fase 3: el alumno entra al nginx por el 8080.
# Fase 4: el mitm SE QUEDA el 8080 y el nginx directo se va al 8081.
$PuertoWebFase3  = 8080
$PuertoWebFase4  = 8081
$PuertoMitmFase4 = 8080

function Rojo     { param($t) Write-Host $t -ForegroundColor Red }
function Verde    { param($t) Write-Host $t -ForegroundColor Green }
function Amarillo { param($t) Write-Host $t -ForegroundColor Yellow }
function Tit      { param($t) Write-Host ""; Write-Host "== $t ==" -ForegroundColor White }

function Comprobar-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Rojo      "No encuentro 'docker'. Instala Docker Desktop para Windows."
        Write-Host "  Si la universidad no te deja instalarlo, usa una maquina virtual:"
        Write-Host "     ver docs\COMO_EJECUTARLO.md"
        exit 1
    }
    docker compose version *> $null
    if ($LASTEXITCODE -ne 0) { Rojo "No encuentro 'docker compose' (v2). Actualiza Docker Desktop."; exit 1 }
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        Rojo      "Docker esta instalado pero no responde."
        Write-Host "  Arranca Docker Desktop y espera a que ponga 'Engine running'."
        Write-Host "  Si tarda o falla, revisa que WSL2 este activo:  wsl --status"
        exit 1
    }
}

function Cmd-Entorno {
    Tit "Donde estas ejecutando el laboratorio"
    Verde "  Windows + Docker Desktop"
    Write-Host "  El navegador de Windows llega a http://localhost:8080 directamente."

    Tit "Docker"
    Comprobar-Docker
    Write-Host "  docker $(docker version --format '{{.Server.Version}}') · compose $(docker compose version --short)"
    try {
        $wsl = wsl --status 2>$null
        if ($wsl) { Write-Host "  WSL disponible (backend recomendado de Docker Desktop)" }
    } catch {}

    Tit "Recursos"
    # Medido: los 5 contenedores usan ~150 MB de RAM y ~1 GB de imagenes en disco.
    try {
        $ramMB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1MB)
        if ($ramMB -lt 2048) { Rojo "  RAM: $ramMB MB - justo. Recomendado 4096 MB" }
        else { Write-Host "  RAM: $ramMB MB  (el lab necesita ~150 MB; de sobra)" }
    } catch {}
    try {
        $libreGB = [math]::Round((Get-PSDrive -Name (Get-Location).Drive.Name).Free / 1GB)
        if ($libreGB -lt 3) { Rojo "  Disco libre: $libreGB GB - insuficiente, el lab descarga ~1 GB" }
        else { Write-Host "  Disco libre: $libreGB GB  (el lab ocupa ~1 GB en imagenes)" }
    } catch {}
}

function Resolver-Pytest {
    $candidatos = @(".venv\Scripts\pytest.exe", ".venv/bin/pytest")
    foreach ($c in $candidatos) { if (Test-Path $c) { return $c } }
    if (Get-Command pytest -ErrorAction SilentlyContinue) { return "pytest" }
    Rojo "No encuentro pytest. Ejecuta primero:  .\lab.ps1 setup"
    exit 1
}

# Nombres de los contenedores Docker que publican un puerto dado ("" si ninguno).
function Quien-Publica {
    param([int]$Puerto)
    $n = docker ps --filter "publish=$Puerto" --format '{{.Names}}' 2>$null
    if (-not $n) { return "" }
    return ($n -join " ").Trim()
}

function Puerto-Ocupado {
    param([int]$Puerto)
    try {
        return [bool](Get-NetTCPConnection -State Listen -LocalPort $Puerto -ErrorAction SilentlyContinue)
    } catch {
        # Fallback si Get-NetTCPConnection no esta disponible
        return [bool]((netstat -an | Select-String ":$Puerto\s.*LISTENING") -ne $null)
    }
}

# Ejecuta docker compose con variables de entorno temporales y las restaura despues.
function Invoke-Compose {
    param([hashtable]$Entorno = @{}, [string[]]$Argumentos)
    $previo = @{}
    foreach ($k in $Entorno.Keys) {
        $previo[$k] = [Environment]::GetEnvironmentVariable($k)
        [Environment]::SetEnvironmentVariable($k, $Entorno[$k])
    }
    try   { & docker compose @Argumentos }
    finally {
        foreach ($k in $previo.Keys) { [Environment]::SetEnvironmentVariable($k, $previo[$k]) }
    }
}

function Cmd-Ayuda {
@"
secure-web-lab - laboratorio de la clase 01, en 4 fases

  entorno         Donde estoy ejecutando esto y que URL uso
  setup           Preparar: .env + entorno virtual + dependencias de test
  fase1-red       Fase 1: estado de tu maquina + esquema de lo que construiremos
  fase1-plan      Solo el esquema de red (para la puesta en comun o consulta)
  fase2-build     Fase 2: construir las imagenes (sin arrancar)
  fase3-web       Fase 3: levantar SOLO la web  -> http://localhost:8080
  test-fase3      Tests de la web . clase 01 (10)
  test-clase02    Tests de HTML y CSS . clase 02 (13)
  test-clase03    Tests de JavaScript . clase 03 (58)
  test-clase04    Tests de NGINX y arquitectura . clase 04 (12)
  test-todo       Todos los tests: clase 01 + clase 02
  fase4-ataque    Fase 4: activar mitm (secuestra el 8080) + sniffer
  credenciales    Las dos capturas juntas: la contrasena en claro
  demo-pasivo     Logs en vivo del sniffer (L3/L4)   . Ctrl+C para salir
  demo-activo     Logs en vivo del mitm (L7)         . Ctrl+C para salir
  estado          Servicios y puertos
  down            Parar y eliminar contenedores
  limpiar         Igual que down, y ademas borra el volumen de la BD

La fase 4 NO tiene tests: es una demostracion. Se comprueba a ojo, mirando
las capturas con 'credenciales', 'demo-pasivo' y 'demo-activo'.

Con los atacantes activos usa SIEMPRE este lanzador: un 'docker compose up -d'
a secas devolveria el 8080 al frontend y chocaria con el mitm.
"@ | Write-Host
}

function Cmd-Setup {
    Cmd-Entorno
    Tit "Variables de entorno"
    if (Test-Path .env) { Write-Host "  .env ya existe (no lo toco)" }
    else { Copy-Item .env.example .env; Verde "  .env creado a partir de .env.example" }

    Tit "Entorno virtual de Python"
    $py = $null
    foreach ($c in @("python", "py", "python3")) {
        if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break }
    }
    if (-not $py) { Rojo "  No encuentro Python 3. Instalalo desde python.org y repite este paso."; exit 1 }

    # Un .venv copiado de otra carpeta guarda rutas absolutas y no funciona.
    if ((Test-Path .venv) -and -not (Test-Path ".venv\Scripts\python.exe")) {
        Write-Host "  .venv inservible (copiado de otra carpeta?): lo recreo"
        Remove-Item -Recurse -Force .venv
    }
    if (-not (Test-Path .venv)) { & $py -m venv .venv }

    & ".venv\Scripts\pip.exe" install -q -r requirements-dev.txt
    $pytest = Resolver-Pytest
    Verde "  $(& $pytest --version) listo"

    Tit "Preparado"
    Write-Host "  Siguiente:  .\lab.ps1 fase1-red"
}

function Cmd-Fase1Red {
    Comprobar-Docker
    Write-Host ""
    Write-Host "######  FASE 1 - PLANIFICAR LA RED  ######" -ForegroundColor White
    Write-Host "--- Parte A: como esta tu maquina AHORA ---" -ForegroundColor White

    Tit "Docker disponible"
    docker version --format '  cliente {{.Client.Version}} / servidor {{.Server.Version}}'
    Write-Host "  compose $(docker compose version --short)"

    Tit "Redes Docker existentes (antes de crear la nuestra)"
    docker network ls

    Tit "Puertos del host que vamos a usar"
    $ajeno = $false; $propio = $false
    foreach ($p in @($PuertoWebFase3, $PuertoWebFase4, 8000)) {
        if (-not (Puerto-Ocupado $p)) { Write-Host "  $p libre"; continue }
        $ocupantes = Quien-Publica $p
        if ($ocupantes -like "secure-web-lab-*") {
            Amarillo "  $p lo tiene TU PROPIO laboratorio ($ocupantes)"
            $propio = $true
        } elseif ([string]::IsNullOrEmpty($ocupantes)) {
            Rojo "  $p OCUPADO por un proceso del host (no es un contenedor)"
            $ajeno = $true
        } else {
            Rojo "  $p OCUPADO por otro contenedor: $ocupantes"
            $ajeno = $true
        }
    }

    if ($propio) {
        Write-Host ""
        Write-Host "  Los puertos en amarillo son de una sesion anterior de este mismo lab."
        Write-Host "  No hay nada que arreglar: las fases siguientes reutilizan esos contenedores."
        Write-Host "  Si prefieres empezar de cero:  .\lab.ps1 down     (o .\lab.ps1 limpiar)"
    }

    if ($ajeno) {
        Write-Host ""
        Rojo      "  Hay puertos ocupados por algo ajeno al laboratorio."
        Write-Host "  Averigua que es y decide tu que hacer (este script no mata procesos):"
        Write-Host "     Get-NetTCPConnection -State Listen -LocalPort 8080 | Select-Object OwningProcess"
        Write-Host "     docker ps --filter publish=8080"
        Write-Host "  Si no puedes liberarlos, cambia FRONTEND_PORT / BACKEND_PORT en .env"
        Write-Host "  (pero entonces las URLs del guion no coincidiran con las tuyas)."
    }

    Write-Host ""
    Write-Host "--- Parte B: lo que vamos a construir ---" -ForegroundColor White
    Cmd-Fase1Plan

    Write-Host "Siguiente paso:"
    Write-Host "  1. Rellena ..\CLASE_01\laboratorio\fase1_plan_de_red.md"
    Write-Host "  2. Cuando este puesto en comun:  .\lab.ps1 fase2-build"
}

# El diseno objetivo. Texto unico en docs\esquema_red.txt, compartido por este
# lanzador y lab.sh (no duplicar, no desincronizar). Comando propio para poder
# reproyectarlo en la puesta en comun o consultarlo en cualquier fase.
function Cmd-Fase1Plan {
    if (Test-Path "docs\esquema_red.txt") {
        Get-Content "docs\esquema_red.txt" -Encoding UTF8 | ForEach-Object { Write-Host $_ }
    } else {
        Rojo "  Falta docs\esquema_red.txt (el esquema de red del laboratorio)."
    }
}

function Cmd-Fase2Build {
    Comprobar-Docker
    docker compose build
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Tit "Imagenes construidas (aun NO hay contenedores corriendo)"
    # Comillas simples: docker espera el literal \t, no un tabulador de PowerShell.
    docker image ls --filter "reference=secure-web-lab-*" --format 'table {{.Repository}}\t{{.Size}}\t{{.CreatedSince}}'
    Write-Host "  Esta fase construye solo la aplicacion: backend y frontend."
    Write-Host "  Las de los atacantes (mitm, sniffer) se construyen en la fase 4;"
    Write-Host "  si aparecen aqui es que ya las tenias de una sesion anterior."
    Tit "Contenedores del proyecto"
    docker compose ps
    Write-Host "  Vacio: una imagen es una receta, no un proceso. Arrancan en la fase 3."
}

function Atacantes-Corriendo {
    $env:COMPOSE_PROFILES = "ataque"
    $svc = docker compose ps --services --filter status=running 2>$null
    $env:COMPOSE_PROFILES = $null
    return (($svc -contains "mitm") -or ($svc -contains "sniffer"))
}

function Cmd-Fase3Web {
    Comprobar-Docker
    # Volver a la fase 3 con la fase 4 activa: el mitm tiene el 8080 y el arranque
    # fallaria con "port is already allocated". Retirar a los atacantes ES volver
    # a la fase 3, asi que lo hacemos nosotros en vez de dar un error criptico.
    if (Atacantes-Corriendo) {
        Amarillo "  Los atacantes estaban activos (fase 4): los retiro para volver a la fase 3."
        Invoke-Compose -Entorno @{COMPOSE_PROFILES="ataque"} -Argumentos @("stop","mitm","sniffer") *> $null
        Invoke-Compose -Entorno @{COMPOSE_PROFILES="ataque"} -Argumentos @("rm","-f","mitm","sniffer") *> $null
    }
    Invoke-Compose -Entorno @{ FRONTEND_PORT = "$PuertoWebFase3" } `
                   -Argumentos @("up", "-d", "--wait", "db", "backend", "frontend")
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host ""
    Verde "  Web:    http://localhost:$PuertoWebFase3"
    Write-Host "  API:    http://localhost:8000/docs"
    Write-Host "  Login:  admin / admin123"
}

function Cmd-Fase4Ataque {
    Comprobar-Docker
    Invoke-Compose -Entorno @{
                        FRONTEND_PORT    = "$PuertoWebFase4"
                        MITM_HOST_PORT   = "$PuertoMitmFase4"
                        COMPOSE_PROFILES = "ataque"
                   } `
                   -Argumentos @("--profile", "ataque", "up", "-d", "--build", "--wait")
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host ""
    Rojo "  http://localhost:$PuertoMitmFase4  -> AHORA pasa por el atacante (mitm L7)"
    Write-Host "  http://localhost:$PuertoWebFase4  -> nginx directo, para comparar"
}

function Cmd-TestFase3   { & (Resolver-Pytest) tests/test_clase01_infra.py -v }
function Cmd-TestClase02 { & (Resolver-Pytest) tests/test_clase02_html_css.py -v }
function Cmd-TestClase03 { & (Resolver-Pytest) tests/test_clase03_js.py -v }
function Cmd-TestClase04 { & (Resolver-Pytest) tests/test_clase04_nginx.py -v }
function Cmd-TestTodo    { & (Resolver-Pytest) tests/ -v }

# La fase 4 es una demostracion, no una suite de tests: se comprueba a ojo.
function Cmd-TestFase4 {
    Rojo "La fase 4 no tiene tests: es una demostracion."
    Write-Host ""
    Write-Host "  Para ver lo que captura el atacante:"
    Write-Host "    .\lab.ps1 credenciales    las dos capturas juntas"
    Write-Host "    .\lab.ps1 demo-pasivo     logs en vivo del sniffer"
    Write-Host "    .\lab.ps1 demo-activo     logs en vivo del mitm"
    Write-Host ""
    Write-Host "  Los tests de la web son:  .\lab.ps1 test-fase3"
}

function Cmd-Credenciales {
    $env:COMPOSE_PROFILES = "ataque"

    Tit "Demo A - sniffer (L3/L4, PASIVO) - bytes crudos del tramo nginx->backend"
    $a = docker compose logs --no-color --tail=400 sniffer 2>$null |
         Select-String -Pattern "password|POST /login" | Select-Object -Last 4
    if ($a) { $a | ForEach-Object { Write-Host $_ } }
    else    { Write-Host "  (sin capturas: haz un login en http://localhost:8080)" }

    Tit "Demo B - mitm (L7, ACTIVO) - HTTP interpretado"
    $b = docker compose logs --no-color --tail=400 mitm 2>$null |
         Select-String -Pattern "MITM-BODY" | Select-Object -Last 4
    if ($b) { $b | ForEach-Object { Write-Host $_ } }
    else    { Write-Host "  (sin capturas: haz un login en http://localhost:8080)" }

    $env:COMPOSE_PROFILES = $null
}

function Cmd-DemoPasivo { Invoke-Compose -Entorno @{COMPOSE_PROFILES="ataque"} -Argumentos @("logs","-f","--tail=50","sniffer") }
function Cmd-DemoActivo { Invoke-Compose -Entorno @{COMPOSE_PROFILES="ataque"} -Argumentos @("logs","-f","--tail=50","mitm") }

function Cmd-Estado {
    Invoke-Compose -Entorno @{COMPOSE_PROFILES="ataque"} `
                   -Argumentos @("ps", "--format", 'table {{.Service}}\t{{.Status}}\t{{.Ports}}')
}

function Cmd-Down    { Invoke-Compose -Entorno @{COMPOSE_PROFILES="ataque"} -Argumentos @("down") }
function Cmd-Limpiar { Invoke-Compose -Entorno @{COMPOSE_PROFILES="ataque"} -Argumentos @("down","-v") }

switch ($Comando) {
    "setup"        { Cmd-Setup }
    "entorno"      { Cmd-Entorno }
    "fase1-red"    { Cmd-Fase1Red }
    "fase1-plan"   { Cmd-Fase1Plan }
    "fase2-build"  { Cmd-Fase2Build }
    "fase3-web"    { Cmd-Fase3Web }
    "test-fase3"   { Cmd-TestFase3 }
    "test-clase02" { Cmd-TestClase02 }
    "test-clase03" { Cmd-TestClase03 }
    "test-clase04" { Cmd-TestClase04 }
    "test-todo"    { Cmd-TestTodo }
    "fase4-ataque" { Cmd-Fase4Ataque }
    "test-fase4"   { Cmd-TestFase4 }
    "credenciales" { Cmd-Credenciales }
    "demo-pasivo"  { Cmd-DemoPasivo }
    "demo-activo"  { Cmd-DemoActivo }
    "estado"       { Cmd-Estado }
    "down"         { Cmd-Down }
    "limpiar"      { Cmd-Limpiar }
    "ayuda"        { Cmd-Ayuda }
    default        { Rojo "Comando desconocido: $Comando"; Write-Host ""; Cmd-Ayuda; exit 1 }
}

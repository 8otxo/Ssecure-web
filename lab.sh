#!/usr/bin/env bash
# ===========================================================================
# secure-web-lab — lanzador del laboratorio (Clase 01, por fases)
#
#   Linux / macOS / WSL / Git Bash:   ./lab.sh <comando>
#   Windows PowerShell:               .\lab.ps1 <comando>   (mismos comandos)
#
# Los nombres de comando son idénticos en los tres lanzadores y en el Makefile.
# ===========================================================================
set -uo pipefail
cd "$(dirname "$0")"

# --- Puertos de cada fase --------------------------------------------------
# Fase 3: el alumno entra al nginx por el 8080.
# Fase 4: el mitm SE QUEDA el 8080 y el nginx directo se va al 8081.
PUERTO_WEB_FASE3=8080
PUERTO_WEB_FASE4=8081
PUERTO_MITM_FASE4=8080

rojo()     { printf '\033[31m%s\033[0m\n' "$*"; }
verde()    { printf '\033[32m%s\033[0m\n' "$*"; }
amarillo() { printf '\033[33m%s\033[0m\n' "$*"; }
tit()      { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

# --- Comprobaciones de entorno --------------------------------------------
comprobar_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    rojo "No encuentro 'docker'."
    echo  "  Windows/macOS: instala Docker Desktop."
    echo  "  Linux:         sudo apt install docker.io docker-compose-v2"
    echo  "  Si no tienes permisos para instalarlo, usa una máquina virtual:"
    echo  "     ver docs/COMO_EJECUTARLO.md"
    exit 1
  fi
  if ! docker compose version >/dev/null 2>&1; then
    rojo "No encuentro 'docker compose' (v2). Actualiza Docker."
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    local err; err=$(docker info 2>&1)
    case "$err" in
      *ermission*denied*)
        rojo "Docker está instalado, pero tu usuario no tiene permiso para usarlo."
        echo  "  Añádete al grupo 'docker' y vuelve a iniciar sesión:"
        echo  "     sudo usermod -aG docker \$USER"
        echo  "  (o ejecuta los comandos con 'sudo' delante)"
        ;;
      *)
        rojo "Docker está instalado pero no responde."
        echo  "  Windows/macOS: arranca Docker Desktop y espera a 'Engine running'."
        echo  "  Linux:         sudo systemctl start docker"
        ;;
    esac
    exit 1
  fi
}

# "nativo" | "mac" | "wsl" | "gitbash" | "vm:<tipo>"
# Da la URL correcta al alumno. Se puede forzar con LAB_ENTORNO=vm:virtualbox
detectar_entorno() {
  if [ -n "${LAB_ENTORNO:-}" ]; then echo "$LAB_ENTORNO"; return; fi
  case "$(uname -s 2>/dev/null)" in
    Darwin) echo "mac"; return ;;
    MINGW*|MSYS*|CYGWIN*) echo "gitbash"; return ;;
  esac
  if grep -qi microsoft /proc/version 2>/dev/null; then echo "wsl"; return; fi
  # OJO: systemd-detect-virt imprime "none" Y sale con código 1 en metal desnudo.
  # Nos quedamos con la primera línea e ignoramos el código de salida.
  local v; v=$(systemd-detect-virt 2>/dev/null | head -1)
  case "${v:-none}" in
    none) echo "nativo" ;;
    *)    echo "vm:$v" ;;
  esac
}

ip_local() { hostname -I 2>/dev/null | awk '{print $1}'; }

# Se imprime junto a las URLs: en una VM, "localhost" no es lo que el alumno cree.
pista_acceso() {
  local puerto="$1"
  case "$(detectar_entorno)" in
    wsl)
      echo "  (WSL2: esa misma URL funciona en el navegador de Windows)" ;;
    vm:*)
      local ip; ip=$(ip_local)
      echo "  Estás dentro de una máquina virtual. Esa URL vale en el navegador"
      echo "  DE LA VM. Desde el navegador de Windows (el anfitrión):"
      echo "     red en PUENTE/bridged →  http://${ip:-<IP-de-la-VM>}:${puerto}"
      echo "     red en NAT            →  reenvía el puerto ${puerto} (docs/COMO_EJECUTARLO.md)"
      ;;
  esac
}

# pytest puede estar en .venv/bin (Unix) o .venv/Scripts (Windows/Git Bash)
resolver_pytest() {
  if   [ -x .venv/bin/pytest ];          then PYTEST=.venv/bin/pytest
  elif [ -x .venv/Scripts/pytest.exe ];  then PYTEST=.venv/Scripts/pytest.exe
  elif command -v pytest >/dev/null 2>&1; then PYTEST=pytest
  else
    rojo "No encuentro pytest. Ejecuta primero:  ./lab.sh setup"
    exit 1
  fi
}

# Nombres de los contenedores Docker que publican un puerto dado (vacío si ninguno).
quien_publica() {
  docker ps --filter "publish=$1" --format '{{.Names}}' 2>/dev/null | tr '\n' ' ' | sed 's/ *$//'
}

puerto_ocupado() {
  local p="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -tln 2>/dev/null | grep -q "[:.]${p} "
  elif command -v netstat >/dev/null 2>&1; then
    netstat -an 2>/dev/null | grep -qiE "[:.]${p}[[:space:]]+.*listen"
  else
    (exec 3<>"/dev/tcp/127.0.0.1/${p}") 2>/dev/null && { exec 3<&- ; return 0; }
    return 1
  fi
}

# --- Comandos --------------------------------------------------------------

cmd_ayuda() {
  cat <<'AYUDA'
secure-web-lab — laboratorio de la clase 01, en 4 fases

  entorno         ¿Dónde estoy ejecutando esto? (VM / WSL / nativo) y qué URL uso
  setup           Preparar: .env + entorno virtual + dependencias de test
  fase1-red       Fase 1: estado de tu máquina + esquema de lo que construiremos
  fase1-plan      Solo el esquema de red (para la puesta en común o consulta)
  fase2-build     Fase 2: construir las imágenes (sin arrancar)
  fase3-web       Fase 3: levantar SOLO la web  -> http://localhost:8080
  test-fase3      Tests de la web · clase 01 (10)
  test-clase02    Tests de HTML y CSS · clase 02 (13)
  test-clase03    Tests de JavaScript · clase 03 (58)
  test-clase04    Tests de NGINX y arquitectura · clase 04 (12)
  test-todo       Todos los tests, de la clase 01 a la 04
  fase4-ataque    Fase 4: activar mitm (secuestra el 8080) + sniffer
  credenciales    Las dos capturas juntas: la contraseña en claro
  demo-pasivo     Logs en vivo del sniffer (L3/L4)   · Ctrl+C para salir
  demo-activo     Logs en vivo del mitm (L7)         · Ctrl+C para salir
  estado          Servicios y puertos
  down            Parar y eliminar contenedores
  limpiar         Igual que down, y además borra el volumen de la BD

La fase 4 NO tiene tests: es una demostración. Se comprueba a ojo, mirando
las capturas con `credenciales`, `demo-pasivo` y `demo-activo`.

Con los atacantes activos usa SIEMPRE este lanzador: un `docker compose up -d`
a secas devolvería el 8080 al frontend y chocaría con el mitm.
AYUDA
}

cmd_entorno() {
  tit "Dónde estás ejecutando el laboratorio"
  local e; e=$(detectar_entorno)
  case "$e" in
    nativo)  verde "  Linux nativo" ;;
    mac)     verde "  macOS" ;;
    wsl)     verde "  WSL2 (Linux dentro de Windows)"
             echo  "  El navegador de Windows llega a http://localhost:8080 sin hacer nada." ;;
    gitbash) verde "  Git Bash sobre Windows (Docker Desktop)" ;;
    vm:*)    amarillo "  Máquina virtual (${e#vm:})"
             echo  "  Es el escenario habitual si no puedes instalar Docker en el equipo."
             echo  "  IP de esta VM: $(ip_local)"
             echo  "  Cómo abrir la web desde Windows: docs/COMO_EJECUTARLO.md" ;;
  esac

  tit "Docker"
  comprobar_docker
  echo "  docker $(docker version --format '{{.Server.Version}}') · compose $(docker compose version --short)"
  if id -nG 2>/dev/null | tr ' ' '\n' | grep -qx docker; then
    echo "  tu usuario está en el grupo 'docker' (no necesitas sudo)"
  fi

  tit "Recursos"
  # El laboratorio medido: ~150 MB de RAM entre los 5 contenedores, ~1 GB de imágenes.
  local ram_mb disco_gb
  ram_mb=$(free -m 2>/dev/null | awk '/^Mem:/{print $2}')
  disco_gb=$(df -BG --output=avail . 2>/dev/null | tail -1 | tr -dc '0-9')
  if [ -n "$ram_mb" ]; then
    if [ "$ram_mb" -lt 2048 ]; then
      rojo     "  RAM: ${ram_mb} MB  — justo. Recomendado 4096 MB (sube la RAM de la VM)"
    else
      echo     "  RAM: ${ram_mb} MB  (el lab necesita ~150 MB; de sobra)"
    fi
  fi
  if [ -n "$disco_gb" ]; then
    if [ "$disco_gb" -lt 3 ]; then
      rojo     "  Disco libre: ${disco_gb} GB — insuficiente. El lab descarga ~1 GB de imágenes"
    else
      echo     "  Disco libre: ${disco_gb} GB  (el lab ocupa ~1 GB en imágenes)"
    fi
  fi
}

cmd_setup() {
  cmd_entorno
  tit "Variables de entorno"
  if [ -f .env ]; then
    echo "  .env ya existe (no lo toco)"
  else
    cp .env.example .env
    verde "  .env creado a partir de .env.example"
  fi

  tit "Entorno virtual de Python"
  local py=""
  for candidato in python3 python py; do
    if command -v "$candidato" >/dev/null 2>&1; then py="$candidato"; break; fi
  done
  if [ -z "$py" ]; then
    rojo "  No encuentro Python 3. Instálalo y repite este paso."
    exit 1
  fi

  # Un .venv copiado de otra carpeta guarda rutas absolutas y no funciona.
  if [ -d .venv ] && ! { [ -x .venv/bin/python ] || [ -x .venv/Scripts/python.exe ]; }; then
    echo "  .venv inservible (¿copiado de otra carpeta?): lo recreo"
    rm -rf .venv
  fi
  [ -d .venv ] || "$py" -m venv .venv

  local pip=".venv/bin/pip"
  [ -x "$pip" ] || pip=".venv/Scripts/pip.exe"
  "$pip" install -q -r requirements-dev.txt
  resolver_pytest
  verde "  $($PYTEST --version 2>&1 | head -1) listo"

  tit "Preparado"
  echo "  Siguiente:  ./lab.sh fase1-red"
}

cmd_fase1_red() {
  comprobar_docker
  printf '\n\033[1m######  FASE 1 · PLANIFICAR LA RED  ######\033[0m\n'
  printf '\033[1m--- Parte A: cómo está tu máquina AHORA ---\033[0m\n'

  tit "Docker disponible"
  docker version --format '  cliente {{.Client.Version}} / servidor {{.Server.Version}}'
  echo "  compose $(docker compose version --short)"

  tit "Redes Docker existentes (antes de crear la nuestra)"
  docker network ls

  tit "Puertos del host que vamos a usar"
  local ajeno=0 propio=0 ocupantes
  for p in "$PUERTO_WEB_FASE3" "$PUERTO_WEB_FASE4" 8000; do
    if ! puerto_ocupado "$p"; then
      echo "  $p libre"
      continue
    fi
    ocupantes=$(quien_publica "$p")
    case "$ocupantes" in
      secure-web-lab-*)
        amarillo "  $p lo tiene TU PROPIO laboratorio ($ocupantes)"
        propio=1 ;;
      "")
        rojo "  $p OCUPADO por un proceso del host (no es un contenedor)"
        ajeno=1 ;;
      *)
        rojo "  $p OCUPADO por otro contenedor: $ocupantes"
        ajeno=1 ;;
    esac
  done

  if [ "$propio" = 1 ]; then
    echo
    echo "  Los puertos en amarillo son de una sesión anterior de este mismo lab."
    echo "  No hay nada que arreglar: las fases siguientes reutilizan esos contenedores."
    echo "  Si prefieres empezar de cero:  ./lab.sh down     (o ./lab.sh limpiar)"
  fi

  if [ "$ajeno" = 1 ]; then
    echo
    rojo  "  Hay puertos ocupados por algo ajeno al laboratorio."
    echo  "  Averigua qué es y decide tú qué hacer (este script no mata procesos):"
    echo  "     ss -tlnp | grep -E ':(8080|8081|8000)'      # proceso del host"
    echo  "     docker ps --filter publish=8080             # contenedor"
    echo  "  Si no puedes liberarlos, cambia FRONTEND_PORT / BACKEND_PORT en .env"
    echo  "  (pero entonces las URLs del guion no coincidirán con las tuyas)."
  fi

  printf '\n\033[1m--- Parte B: lo que vamos a construir ---\033[0m\n'
  cmd_fase1_plan

  echo "Siguiente paso:"
  echo "  1. Rellena ../CLASE_01/laboratorio/fase1_plan_de_red.md"
  echo "  2. Cuando esté puesto en común:  ./lab.sh fase2-build"
}

# El diseño objetivo. Texto único en docs/esquema_red.txt, compartido por este
# lanzador y lab.ps1 (no duplicar, no desincronizar). Comando propio para poder
# reproyectarlo en la puesta en común o consultarlo en cualquier fase.
cmd_fase1_plan() {
  if [ -f docs/esquema_red.txt ]; then
    cat docs/esquema_red.txt
  else
    rojo "  Falta docs/esquema_red.txt (el esquema de red del laboratorio)."
  fi
}

cmd_fase2_build() {
  comprobar_docker
  docker compose build || exit 1
  tit "Imágenes construidas (aún NO hay contenedores corriendo)"
  docker image ls --filter "reference=secure-web-lab-*" \
    --format "table {{.Repository}}\t{{.Size}}\t{{.CreatedSince}}"
  echo "  Esta fase construye solo la aplicación: backend y frontend."
  echo "  Las de los atacantes (mitm, sniffer) se construyen en la fase 4;"
  echo "  si aparecen aquí es que ya las tenías de una sesión anterior."
  tit "Contenedores del proyecto"
  docker compose ps
  echo "  Vacío: una imagen es una receta, no un proceso. Arrancan en la fase 3."
}

atacantes_corriendo() {
  COMPOSE_PROFILES=ataque docker compose ps --services --filter status=running 2>/dev/null \
    | grep -qE '^(mitm|sniffer)$'
}

cmd_fase3_web() {
  comprobar_docker
  # Volver a la fase 3 con la fase 4 activa: el mitm tiene el 8080 y el arranque
  # fallaría con "port is already allocated". Retirar a los atacantes ES volver
  # a la fase 3, así que lo hacemos nosotros en vez de dar un error críptico.
  if atacantes_corriendo; then
    amarillo "  Los atacantes estaban activos (fase 4): los retiro para volver a la fase 3."
    COMPOSE_PROFILES=ataque docker compose stop mitm sniffer >/dev/null 2>&1
    COMPOSE_PROFILES=ataque docker compose rm -f mitm sniffer >/dev/null 2>&1
  fi
  FRONTEND_PORT="$PUERTO_WEB_FASE3" docker compose up -d --wait db backend frontend || exit 1
  echo
  verde "  Web:    http://localhost:${PUERTO_WEB_FASE3}"
  echo  "  API:    http://localhost:8000/docs"
  echo  "  Login:  admin / admin123"
  pista_acceso "$PUERTO_WEB_FASE3"
}

cmd_fase4_ataque() {
  comprobar_docker
  FRONTEND_PORT="$PUERTO_WEB_FASE4" \
  MITM_HOST_PORT="$PUERTO_MITM_FASE4" \
  COMPOSE_PROFILES=ataque \
    docker compose --profile ataque up -d --build --wait || exit 1
  echo
  rojo  "  http://localhost:${PUERTO_MITM_FASE4}  -> AHORA pasa por el atacante (mitm L7)"
  echo  "  http://localhost:${PUERTO_WEB_FASE4}  -> nginx directo, para comparar"
  pista_acceso "$PUERTO_MITM_FASE4"
}

cmd_test_fase3()   { resolver_pytest; "$PYTEST" tests/test_clase01_infra.py -v; }
cmd_test_clase02() { resolver_pytest; "$PYTEST" tests/test_clase02_html_css.py -v; }
cmd_test_clase03() { resolver_pytest; "$PYTEST" tests/test_clase03_js.py -v; }
cmd_test_clase04() { resolver_pytest; "$PYTEST" tests/test_clase04_nginx.py -v; }
cmd_test_todo()    { resolver_pytest; "$PYTEST" tests/ -v; }

# La fase 4 es una demostración, no una suite de tests: se comprueba a ojo.
cmd_test_fase4() {
  rojo "La fase 4 no tiene tests: es una demostración."
  echo
  echo "  Para ver lo que captura el atacante:"
  echo "    ./lab.sh credenciales    las dos capturas juntas"
  echo "    ./lab.sh demo-pasivo     logs en vivo del sniffer"
  echo "    ./lab.sh demo-activo     logs en vivo del mitm"
  echo
  echo "  Los tests de la web son:  ./lab.sh test-fase3"
}

cmd_credenciales() {
  local logs
  tit "Demo A · sniffer (L3/L4, PASIVO) — bytes crudos del tramo nginx->backend"
  logs=$(COMPOSE_PROFILES=ataque docker compose logs --no-color --tail=400 sniffer 2>/dev/null \
         | grep -iE "password|POST /login" | tail -4)
  [ -n "$logs" ] && echo "$logs" || echo "  (sin capturas: haz un login en http://localhost:8080)"

  tit "Demo B · mitm (L7, ACTIVO) — HTTP interpretado"
  logs=$(COMPOSE_PROFILES=ataque docker compose logs --no-color --tail=400 mitm 2>/dev/null \
         | grep "MITM-BODY" | tail -4)
  [ -n "$logs" ] && echo "$logs" || echo "  (sin capturas: haz un login en http://localhost:8080)"
}

cmd_demo_pasivo() { COMPOSE_PROFILES=ataque docker compose logs -f --tail=50 sniffer; }
cmd_demo_activo() { COMPOSE_PROFILES=ataque docker compose logs -f --tail=50 mitm; }

cmd_estado() {
  COMPOSE_PROFILES=ataque docker compose ps \
    --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
}

cmd_down()    { COMPOSE_PROFILES=ataque docker compose down; }
cmd_limpiar() { COMPOSE_PROFILES=ataque docker compose down -v; }

# --- Despacho --------------------------------------------------------------
case "${1:-ayuda}" in
  setup)         cmd_setup ;;
  entorno)       cmd_entorno ;;
  fase1-red)     cmd_fase1_red ;;
  fase1-plan)    cmd_fase1_plan ;;
  fase2-build)   cmd_fase2_build ;;
  fase3-web)     cmd_fase3_web ;;
  test-fase3)    cmd_test_fase3 ;;
  test-clase02)  cmd_test_clase02 ;;
  test-clase03)  cmd_test_clase03 ;;
  test-clase04)  cmd_test_clase04 ;;
  test-todo)     cmd_test_todo ;;
  fase4-ataque)  cmd_fase4_ataque ;;
  test-fase4)    cmd_test_fase4 ;;
  credenciales)  cmd_credenciales ;;
  demo-pasivo)   cmd_demo_pasivo ;;
  demo-activo)   cmd_demo_activo ;;
  estado)        cmd_estado ;;
  down)          cmd_down ;;
  limpiar)       cmd_limpiar ;;
  ayuda|-h|--help|help) cmd_ayuda ;;
  *) rojo "Comando desconocido: $1"; echo; cmd_ayuda; exit 1 ;;
esac

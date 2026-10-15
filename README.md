# secure-web-lab

Laboratorio acumulativo de **Desarrollo Web Seguro** (EUNEIZ 2026-2027).

Aplicación web intencionalmente insegura al inicio; cada semana se añaden controles y tests.

## Requisitos

- **Linux/macOS:** Docker 24+ y Docker Compose v2
- **Windows:** Docker Desktop con backend **WSL2** activado
- Python 3.11+ (tests en el host)
- Node.js 20+ (desde clase 3)

## Cómo se lanza

Hay un lanzador por sistema, con **los mismos nombres de comando** en todos:

| Sistema | Comando |
|---------|---------|
| Linux / macOS / WSL | `make <comando>` o `./lab.sh <comando>` |
| Windows PowerShell | `.\lab.ps1 <comando>` |
| Windows con WSL o Git Bash | `./lab.sh <comando>` |

Empieza siempre por `setup`, que crea el `.env`, el entorno virtual e instala las
dependencias de test:

```bash
make setup          # Windows:  .\lab.ps1 setup
```

## Inicio rápido — el lab se monta por fases

```bash
make fase1-red      # 1. Ver la red y los puertos ANTES de crear nada
make fase2-build    # 2. Construir las imágenes (aún no arranca nada)
make fase3-web      # 3. La web: db + backend + frontend  -> http://localhost:8080
make test-fase3     #    10 tests de la aplicación (clase 01)
make test-clase02   #    13 tests de HTML y CSS (clase 02)

make fase4-ataque   # 4. Activar los atacantes: el mitm SECUESTRA el 8080
make credenciales   #    la contraseña en claro, capturada por los dos atacantes
make demo-pasivo    #    logs del sniffer (L3/L4)   ·  make demo-activo (mitm, L7)

make estado         # ver servicios y puertos   ·  make down para parar
```

En la fase 4 los puertos se intercambian a propósito: `8080` pasa a ser el
atacante (misma URL que ya usaba el alumno, sin avisar) y el nginx directo queda
en `8081` para poder comparar. Ver [`practica_guiada.md`](../CLASE_01/laboratorio/practica_guiada.md).

> Si copias este repo de un curso anterior, **borra y recrea `.venv`**: un entorno
> virtual guarda rutas absolutas y se rompe al renombrar la carpeta. `make setup`
> lo detecta y lo hace por ti.

---

# Guion de clase

Qué decir y qué hace cada comando por dentro. El guion de la **fase 1** está en
[`fase1_plan_de_red.md`](../CLASE_01/laboratorio/fase1_plan_de_red.md) y en el
propio `make fase1-red`; aquí van las fases 2, 3 y 4.

## FASE 2 — Construir los contenedores (25 min)

**Idea que tienen que llevarse:** una imagen es una receta congelada; un
contenedor es un proceso vivo. Construir no es arrancar.

### 2.1 — Leer un Dockerfile (5 min)

Abre `backend/Dockerfile` en el proyector. Son cinco instrucciones:

| Instrucción | Cuándo actúa | Qué hace |
|-------------|--------------|----------|
| `FROM python:3.12-slim` | al construir | De qué imagen partimos |
| `WORKDIR /app` | al construir | Carpeta de trabajo dentro del contenedor |
| `COPY requirements.txt .` | al construir | Mete archivos del proyecto en la imagen |
| `RUN pip install -r ...` | al construir | Ejecuta algo y **lo graba** en la imagen |
| `CMD ["uvicorn", ...]` | al **ejecutar** | El proceso que arranca al crear un contenedor |

Dos ideas de seguridad que ya se ven aquí: `-slim`/`-alpine` significan menos
paquetes instalados, o sea **menos vulnerabilidades heredadas** (A02, y A03 si la
imagen base viene comprometida); y `EXPOSE 8000` **no abre nada** al host, solo
documenta — quien abre es `ports:` en el compose.

### 2.2 — Construir

```bash
make fase2-build
```

**Qué ejecuta por dentro:** `docker compose build`. Lee el `Dockerfile` de
`backend` y `frontend`, descarga las imágenes base si no están, ejecuta las
instrucciones y guarda el resultado como imagen local. **No arranca nada.**

Solo construye la aplicación: `mitm` y `sniffer` están tras el perfil `ataque` y
se construyen en la fase 4.

> La primera vez tarda varios minutos: descarga ~1 GB. Aprovecha para el paso
> 2.1, o pídeles que lo hagan en casa la víspera.

Al terminar verás dos bloques. El segundo es el importante:

```
== Contenedores del proyecto ==
  (vacío)
  Vacío: una imagen es una receta, no un proceso. Arrancan en la fase 3.
```

*Hemos construido cuatro recetas y no hay ni un solo proceso corriendo.*

### 2.3 — Demo: un contenedor suelto no es una aplicación (5 min)

```bash
docker build -t demo-clase1 -f nginx/Dockerfile .
docker run --rm --name demo-solo demo-clase1
```

`docker build -t <nombre> -f <Dockerfile> .` construye a mano lo que Compose hacía
por ti. `docker run` crea **un** contenedor de esa imagen; `--rm` lo borra al
salir. Y falla:

```
nginx: [emerg] host not found in upstream "backend"
```

Pregunta a la clase: *¿por qué?* Porque `backend` es un **nombre de red**, y sin
la red del laboratorio ese nombre no existe. Ahora dentro de la red:

```bash
docker run --rm -d --name demo-red --network secure-web-lab_web_net -p 9090:80 demo-clase1
curl -s http://localhost:9090 | head -3
docker stop demo-red && docker rmi demo-clase1
```

`--network` lo mete en la red del lab (donde `backend` sí resuelve), `-d` lo deja
en segundo plano y `-p 9090:80` publica el puerto 80 del contenedor en el 9090 de
tu máquina. Ahora sí responde.

**Conclusión:** lo que aporta Compose no es «arrancar cosas», es **crear las redes
y resolver los nombres** que planificaron en la fase 1.

### 2.4 — El compose es su plan, en YAML (8 min)

Abre `docker-compose.yml` y que localicen sus decisiones:

| En el YAML | Es la decisión de la fase 1 |
|------------|------------------------------|
| `db:` sin `ports` | La BD no se publica al host |
| `backend: ports: 8000` | Deuda declarada: ruta que evita el proxy |
| `frontend: ports: "${FRONTEND_PORT:-8080}:80"` | Punto de entrada (8080 del host → 80 del contenedor) |
| `networks: ruta_usuario` / `web_net` | Los dos segmentos |
| `frontend` en **ambas** redes | El único puente entre fuera y dentro |
| `depends_on: service_healthy` | La API no arranca hasta que la BD responde |
| `profiles: ["ataque"]` | Los atacantes **no** arrancan todavía |

**✋ Checkpoint:** saben decir qué línea publica un puerto y cuál solo lo documenta.

---

## FASE 3 — La web viva (20 min)

**Idea:** que usen la aplicación con normalidad. Sin este «antes», la fase 4 no
impresiona a nadie.

### 3.1 — Levantar solo la aplicación

```bash
make fase3-web
```

**Qué ejecuta por dentro:** `docker compose up -d --wait db backend frontend`.

- `up` crea los contenedores a partir de las imágenes de la fase 2
- `-d` los deja en segundo plano (te devuelve la terminal)
- `--wait` **espera a que estén sanos** antes de darte el control: nada de
  «parece que arrancó pero la BD aún no aceptaba conexiones»
- nombrar los tres servicios deja fuera a los atacantes

Si venías de la fase 4, retira los atacantes él solo y te lo dice.

```bash
make estado
```

Es `docker compose ps`. Que comparen la columna `PORTS` con la tabla que
rellenaron en la fase 1:

```
backend    0.0.0.0:8000->8000/tcp     ← la deuda que declararon
db         5432/tcp                   ← sin publicar, como decidieron
frontend   0.0.0.0:8080->80/tcp       ← el 8080 del host entra por el 80
```

### 3.2 — Que entren

| Servicio | URL | Qué verán |
|----------|-----|-----------|
| Web | http://localhost:8080 | Login |
| API | http://localhost:8000/docs | Swagger (la deuda declarada) |
| BD | `localhost:5432` | **Rechazado** |

Login `admin` / `admin123` → bienvenida a la clase.

Merece treinta segundos en F12 → Network: el POST devuelve **303 See Other** y a
continuación hay un **GET** a `/panel.html`. Sin JavaScript (llega en la clase
3), el redirect lo tiene que hacer el servidor: es el patrón POST-Redirect-GET.

### 3.3 — Observar antes de atacar (8 min)

En parejas, con F12 abierto, responden por escrito:

1. ¿HTTP o HTTPS?
2. En `POST /api/login`, ¿qué se ve exactamente en **Payload**?
3. `curl -v http://localhost:8080` — ¿qué cabeceras de seguridad faltan?
   (`-v` muestra cabeceras de petición y respuesta; busca HSTS, CSP, X-Frame-Options)
4. La cookie `session_id`: ¿qué valor tiene? ¿lo puedes adivinar?

> Ya están viendo su contraseña en claro **en su propio navegador**. La pregunta
> que abre la fase 4 es: *¿quién más puede ver esto?*

### 3.4 — Opcional: la salida a Internet (2 min)

```bash
docker compose exec db wget -q -O /dev/null -T5 http://example.com && echo "la BD sale a Internet"
```

`docker compose exec <servicio> <comando>` ejecuta algo **dentro** de un
contenedor que ya corre. Y sí, sale: la BD no tiene puerto publicado —nadie entra—
pero puede salir. Entrada y salida son problemas distintos: la primera es por
dónde te atacan, la segunda por dónde se llevan los datos.

### 3.5 — Tests

```bash
make test-fase3
```

Es `pytest tests/test_clase01_infra.py -v` con el `pytest` del `.venv` (no hace
falta activarlo). Esperado: **7 passed**.

Abre el archivo y enseña que cada test es una frase del plan de red convertida en
código — `test_db_not_published_to_host` es literalmente la decisión que tomaron
en papel. **Eso es DevSecOps**: la decisión de diseño se verifica sola.

Y uno de ellos, `test_no_https_on_frontend`, está en verde porque el laboratorio
es inseguro. Hoy eso es lo correcto.

**✋ Checkpoint:** web abierta, login hecho, 7/7 en verde. **No sigas hasta aquí
completo**: la fase 4 solo tiene sentido si la web ya les funcionaba.

---

## FASE 4 — Los atacantes (30 min)

**Antes de tocar nada, avísales.** Con la web abierta en su pestaña:

> «No cerréis la pestaña. No cambiéis la URL. Voy a activar dos contenedores y
> vais a hacer login otra vez, igual que hace cinco minutos. Después me decís si
> habéis notado algo.»

```bash
make fase4-ataque
make estado
```

`fase4-ataque` ejecuta `docker compose --profile ataque up -d --build --wait` con
los puertos intercambiados. `--profile ataque` incluye por fin a `mitm` y
`sniffer`; `--build` los construye la primera vez. En `estado` verán el 8080
cambiar de dueño:

```
frontend   0.0.0.0:8081->80      ← el nginx se aparta
mitm       0.0.0.0:8080->8080    ← el atacante OCUPA la URL del alumno
sniffer                          ← sin puerto: solo escucha
```

**Ellos recargan y hacen login.** *¿Alguien ha notado algo?* Nadie: ni aviso, ni
error de certificado — no hay certificado que validar, van en HTTP.

```bash
make credenciales
```

Lee los logs de los dos atacantes y filtra la contraseña:

```
== Demo A · sniffer (L3/L4, PASIVO) ==
sniffer-1  | POST /login HTTP/1.0
sniffer-1  | username=admin&password=admin123

== Demo B · mitm (L7, ACTIVO) ==
mitm-1  | [MITM-BODY] http://frontend/api/login -> username=admin&password=admin123
```

La misma contraseña por dos caminos independientes. *¿Cuál de los dos ha tenido
que romper algo?* Ninguno: solo estar donde había que estar.

**El detalle que sorprende:** lo que ve el sniffer no es el tráfico del navegador,
es el tramo interno `nginx → backend`. El que casi nadie marcó como «sin cifrar»
en la fase 1. No falta cifrado solo hacia fuera: falta dentro.

```bash
curl -s -o /dev/null -w "8080 atacante: %{http_code}\n" http://localhost:8080
curl -s -o /dev/null -w "8081 limpio:   %{http_code}\n" http://localhost:8081
```

Idénticas. **Sin criptografía no hay forma de saber con quién hablas** — eso es lo
que resuelve TLS, no «cifrar por cifrar».

Opcional, la lección de segmentación:

```bash
docker compose exec mitm python3 -c "import socket; socket.create_connection(('db',5432),timeout=3)"
# socket.gaierror  → lo lee TODO y no tiene ni ruta hasta la base de datos
```

Interponerse no es lo mismo que estar dentro.

> **La fase 4 no tiene tests, y es a propósito.** Es una demostración: sirve
> para *ver* la contraseña viajando en claro, no para verificar el proyecto.
> Lo que aquí se comprueba se comprueba a ojo, con `make credenciales`.
>
> La frase de cierre: **el laboratorio es inseguro, y hoy lo hemos visto**.
> A partir de la clase 7 (HTTPS) esta demo dejará de funcionar, y ese fallo
> será la prueba de que el control funciona.

Para dejar la máquina limpia: `make down` (conserva la BD) o `make limpiar`
(borra también el volumen).

## Notas para Windows

| Situación | Qué hacer |
|-----------|-----------|
| PowerShell bloquea el script | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| Comandos `curl` del guion | En PowerShell usa **`curl.exe`**: `curl` a secas es `Invoke-WebRequest` y no entiende `-s -X -d` |
| `exec /sniff.sh: no such file or directory` | Los `.sh` llegaron con finales de línea CRLF. El `.gitattributes` lo evita al clonar; si descargaste un ZIP, conviértelos a LF |
| `docker: error during connect` | Docker Desktop no arrancado, o falta el backend WSL2 |

Los contenedores corren dentro de la VM Linux de WSL2, así que el laboratorio se
comporta igual que en Linux. **Conviene probar una vez el `sniffer` en un equipo
Windows real antes de clase:** necesita `NET_RAW` y compartir el *network
namespace* del backend. Si en algún equipo no capturase, los tests lo marcan como
`SKIPPED` en vez de fallar, y la Demo B (mitm) sigue funcionando.

## Credenciales demo (clase 1 — inseguras)

| Usuario | Contraseña |
|---------|------------|
| admin   | admin123   |

## Estructura

```
secure-web-lab/
├── lab.sh            # Lanzador Linux/macOS/WSL (lógica real)
├── lab.ps1           # Lanzador Windows PowerShell (mismos comandos)
├── Makefile          # Atajo: delega en lab.sh
├── backend/          # FastAPI (API + lógica)
├── frontend/         # HTML estático servido por NGINX
├── nginx/            # Configuración reverse proxy
├── mitm/             # Atacante ACTIVO L7: proxy mitmproxy (Demo B, solo lab)
├── sniffer/          # Atacante PASIVO L3/L4: tcpdump (Demo A, solo lab)
├── tests/            # pytest + (clase 3+) Vitest/Playwright
└── docs/             # Informes y checklist OWASP
```

> **Tres contenedores + dos atacantes:** `db`, `backend` y `frontend` son la
> aplicación; `mitm` y `sniffer` son el atacante y viven tras el perfil de Compose
> `ataque`, así que un `docker compose up` normal **no los arranca**. El *porqué*
> de cada decisión y sus alternativas: [`CLASE_01/laboratorio/arquitectura_y_decisiones.md`](../CLASE_01/laboratorio/arquitectura_y_decisiones.md).

## Versiones por clase

| Tag | Contenido |
|-----|-----------|
| v0.1 | Lab Docker + MITM + login HTML |
| v0.2 | HTML/CSS semántico + accesibilidad |
| v0.3 | JavaScript + Vitest |
| … | Ver README del curso |

## Chuleta: todos los comandos en orden

Para tener al lado durante la clase. En Windows, `make X` → `.\lab.ps1 X`.

```bash
# ── Preparación (una vez) ────────────────────────────────────────────────
make setup                  # entorno, .env, venv, dependencias

# ── FASE 1 · Planificar la red ───────────────────────────────────────────
make fase1-red              # estado de la máquina + esquema de lo que se construirá
#                             (make fase1-plan = solo el esquema, para la puesta en común)

# ── FASE 2 · Construir ───────────────────────────────────────────────────
make fase2-build            # construye las imágenes; NO arranca nada

docker build -t demo-clase1 -f nginx/Dockerfile .          # demo opcional:
docker run --rm --name demo-solo demo-clase1               #   falla sin red
docker run --rm -d --name demo-red \
  --network secure-web-lab_web_net -p 9090:80 demo-clase1  #   con red, funciona
curl -s http://localhost:9090 | head -3
docker stop demo-red && docker rmi demo-clase1

# ── FASE 3 · La web viva ─────────────────────────────────────────────────
make fase3-web              # levanta db + backend + frontend
make estado                 # comprobar puertos
#   navegador: http://localhost:8080   ·  login admin / admin123
curl -v http://localhost:8080                              # faltan cabeceras
docker compose exec db wget -q -O /dev/null -T5 http://example.com && echo "la BD sale a Internet"
make test-fase3             # 7/7

# ── FASE 4 · Los atacantes ───────────────────────────────────────────────
#   ANTES: "no cerréis la pestaña, no cambiéis la URL"
make fase4-ataque           # mitm ocupa el 8080; el nginx pasa al 8081
make estado                 # ver el cambio de dueño del 8080
#   ELLOS: recargan y hacen login otra vez
make credenciales           # la contraseña, capturada por los dos atacantes
curl -s -o /dev/null -w "8080 atacante: %{http_code}\n" http://localhost:8080
curl -s -o /dev/null -w "8081 limpio:   %{http_code}\n" http://localhost:8081
docker compose exec mitm python3 -c "import socket; socket.create_connection(('db',5432),timeout=3)"
#   La fase 4 es una demo: no tiene tests, se comprueba a ojo

# ── Cierre ───────────────────────────────────────────────────────────────
make down                   # parar (conserva la BD)
make limpiar                # parar y borrar también el volumen de datos
```

En vivo, en una segunda terminal: `make demo-pasivo` (sniffer) o
`make demo-activo` (mitm), Ctrl+C para salir.

## Aviso legal

Los contenedores `mitm` y `sniffer`, y las vulnerabilidades deliberadas, son **solo para educación** en la red Docker aislada del laboratorio. No usar en producción ni contra redes ajenas al laboratorio.

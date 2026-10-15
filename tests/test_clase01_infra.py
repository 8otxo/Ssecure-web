"""
═══════════════════════════════════════════════════════════════════════════════
TESTS DE LA APLICACIÓN — Clase 01 (fase 3)
═══════════════════════════════════════════════════════════════════════════════

Comprueban que la web funciona y que la red es la que diseñamos en la fase 1.

    make fase3-web        (levanta db + backend + frontend)
    make test-fase3       (ejecuta este archivo)

───────────────────────────────────────────────────────────────────────────────
CÓMO FUNCIONA ESTO (léelo antes que el código)
───────────────────────────────────────────────────────────────────────────────

Este archivo NO se ejecuta como un programa normal. No hay `main`, y nadie
llama a estas funciones. Lo que ocurre es:

1. Escribes `pytest tests/test_clase01_infra.py`
2. Pytest IMPORTA el archivo y busca toda función que empiece por `test_`
3. Las ejecuta una a una, cada una aislada de las demás
4. Si una termina sin reventar  → PASSED
Si un `assert` falla         → FAILED

Eso es todo el framework. Las funciones que NO empiezan por `test_` (los
"ayudantes") pytest ni las mira: están ahí para que tú las reutilices.

La forma de un test es siempre la misma, se llama patrón AAA:

    def test_lo_que_sea():
        dato = <consigo información>         # 1. Preparar / Actuar
        assert dato == <lo que debería ser>  # 2. Comprobar

`assert <condición>, "mensaje"` → si la condición es falsa, el test falla y
muestra TU mensaje. Pon siempre el mensaje: es lo que leerás cuando algo se
rompa dentro de tres semanas.

───────────────────────────────────────────────────────────────────────────────
LOS CINCO RESULTADOS POSIBLES DE UN TEST
───────────────────────────────────────────────────────────────────────────────

    PASSED   El requisito se cumple. Todo bien.
    FAILED   El requisito NO se cumple. Algo está roto y no lo sabías.
    SKIPPED  No se pudo comprobar (falta Docker, el lab está parado...).
            OJO: saltado NO es aprobado. Si ves SKIPPED, investiga.
    XFAIL    Falla, pero estaba previsto: es una deuda registrada a propósito.
    XPASS    ¡Ya funciona lo que estaba marcado como deuda! Toca quitar la marca.

───────────────────────────────────────────────────────────────────────────────
DOS TIPOS DE TEST: ESTÁTICOS Y DINÁMICOS
───────────────────────────────────────────────────────────────────────────────

Cada test de este archivo lleva la etiqueta [ESTÁTICO] o [DINÁMICO] delante.
La diferencia es de dónde saca la información:

    [ESTÁTICO]  Lee el docker-compose.yml. NO necesita Docker ni el laboratorio
                encendido. Tarda milisegundos. Responde a la pregunta:
                        «¿qué hemos PEDIDO que exista?»
                En la tubería DevSecOps es el equivalente al SAST: analizar el
                código fuente sin ejecutarlo.

    [DINÁMICO]  Interroga al laboratorio EN MARCHA: pregunta a Docker o hace
                peticiones HTTP de verdad. Necesita `make fase3-web` antes.
                Responde a la pregunta:
                        «¿qué hay REALMENTE funcionando?»
                Es el equivalente al DAST: probar el sistema vivo.

¿Por qué hacen falta los dos? Verás dos tests que parecen el mismo:

    test_estatico_la_bd_no_declara_puertos   ← lo que pide el fichero
    test_dinamico_la_bd_no_esta_publicada    ← lo que hace el contenedor

No son un duplicado. Si alguien levanta la BD a mano con `-p 5432:5432`, el
fichero seguirá diciendo que todo está bien y solo el dinámico lo cazará. Y al
revés: si alguien mete un `ports:` en el YAML pero nadie ha reiniciado, solo el
estático lo ve venir. Cuando los dos no coinciden se llama DRIFT de
configuración, y es una causa clásica de incidentes.

───────────────────────────────────────────────────────────────────────────────
QUÉ HAY EN ESTE ARCHIVO (10 tests)
───────────────────────────────────────────────────────────────────────────────

IMPRESCINDIBLES (7) → si uno falla, la aplicación está rota o mal diseñada
    2 estáticos  · la BD no declara puertos · cada servicio en su red
    5 dinámicos  · servicios sanos · BD no publicada · el frontend sirve
                    · el login correcto entra · el login incorrecto NO entra

EXTRA (3, todos dinámicos) → documentan vulnerabilidades deliberadas de hoy
    Están en verde PORQUE el laboratorio es inseguro, y eso es correcto en la
    clase 1. A partir de la clase 7 (HTTPS) empezarán a fallar, y ese fallo
    será la prueba de que el control funciona.
"""

# ══════════════════════════════════════════════════════════════════════════════
#  1 · IMPORTS — qué herramientas necesitamos y para qué
# ══════════════════════════════════════════════════════════════════════════════

# Librería estándar de Python (viene con Python, no hay que instalar nada):
import json         # Docker nos responde con texto JSON; esto lo convierte en diccionario
import os           # Leer variables de entorno y construir rutas de carpetas
import subprocess   # Ejecutar el comando `docker` desde Python, como en una terminal

# Paquetes instalados con pip (están en requirements-dev.txt):
import httpx        # Cliente HTTP: es `curl`, pero desde Python
import pytest       # El framework de tests. Aquí solo usamos pytest.skip y pytest.fixture
import yaml         # Leer el docker-compose.yml (lo usan los tests ESTÁTICOS)

# Nota: de los cinco, solo `pytest` tiene que ver con "hacer tests". Los otros
# cuatro están porque, para comprobar nuestra arquitectura, hay que hablar con
# Docker y con la web.


# ══════════════════════════════════════════════════════════════════════════════
#  2 · CONSTANTES — valores que se repiten, en un solo sitio
# ══════════════════════════════════════════════════════════════════════════════

# os.getenv("NOMBRE", "por_defecto") significa:
#   "si existe una variable de entorno llamada NOMBRE, úsala; si no, usa esto".
# En la práctica siempre coge el valor por defecto. Está así para poder lanzar
# los mismos tests contra otra dirección sin tocar el código.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")
# Hasta la clase 03 esto apuntaba a http://localhost:8000: la ruta directa al
# backend, saltándose el proxy. En la clase 04 ese puerto se cierra, así que
# la comprobación pasa por la puerta principal, como cualquier usuario.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080/api")
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "admin123")

# Ruta a la carpeta del laboratorio. Se lee de dentro afuera:
#   __file__                              → .../secure-web-lab/tests/test_clase01_infra.py
#   os.path.dirname(...)                  → .../secure-web-lab/tests
#   os.path.dirname(os.path.dirname(...)) → .../secure-web-lab
# Hace falta porque `docker compose` debe ejecutarse donde está el
# docker-compose.yml. Calculándolo así, funciona lances pytest desde donde lo lances.
LAB_DIR = os.path.dirname(os.path.dirname(__file__))

# El fichero que describe toda la arquitectura. Los tests ESTÁTICOS lo leen.
RUTA_COMPOSE = os.path.join(LAB_DIR, "docker-compose.yml")

# La segmentación de red que diseñamos en la fase 1:
#   ruta_usuario = el camino por el que llega el usuario
#   web_net      = la red privada (backend y base de datos)
# El frontend es el único con un pie en cada una: es el punto de entrada.
REDES_ESPERADAS = {
    "db": {"web_net"},
    "backend": {"web_net"},
    "frontend": {"ruta_usuario", "web_net"},
}


# ══════════════════════════════════════════════════════════════════════════════
#  3 · AYUDANTES — la fontanería para leer el YAML y hablar con Docker
# ══════════════════════════════════════════════════════════════════════════════
# El guion bajo del principio (_compose) es una convención de Python: "esto es
# interno". Y como no empiezan por `test_`, pytest no los ejecuta como tests.

def _leer_compose():
    """Lee el docker-compose.yml y lo devuelve como diccionario de Python.

    Lo usan los tests ESTÁTICOS. Aquí no se ejecuta nada: solo se abre un
    archivo de texto y se traduce. Por eso funciona con el laboratorio apagado.
    """
    with open(RUTA_COMPOSE, encoding="utf-8") as fichero:
        # yaml.safe_load convierte el texto YAML en diccionarios y listas.
        # Se usa "safe_load" y no "load" por seguridad: `load` a secas puede
        # ejecutar código si el YAML viene manipulado. Nunca uses load().
        return yaml.safe_load(fichero)

def _compose(*args, timeout=30):
    """Ejecuta `docker compose <lo que le pases>` y devuelve el resultado.

    Ejemplo: _compose("ps", "--format", "json")
            ejecuta:  docker compose ps --format json
    """
    # *args recoge todas las palabras extra que le pasen: ("ps", "--format", "json").
    # El *args de dentro de la lista las DESEMPAQUETA, construyendo:
    #   ["docker", "compose", "ps", "--format", "json"]
    # subprocess.run ejecuta esa orden, palabra por palabra, igual que si la
    # escribieras en la terminal. Pero NO abre ninguna terminal ni imprime nada:
    # ejecuta el programa directamente y nos guarda su salida.
    return subprocess.run(
        ["docker", "compose", *args],
        capture_output=True,  # No imprimas en pantalla: dame la salida en una variable
        text=True,            # Dámela como texto (str), no como bytes
        timeout=timeout,      # Si se queda colgado, aborta a los 30 segundos
        cwd=LAB_DIR,          # Ejecuta el comando EN la carpeta del laboratorio
    )
    # Lo que devuelve tiene tres cosas útiles:
    #   .stdout      → lo que el comando imprimió (texto)
    #   .stderr      → los errores
    #   .returncode  → 0 si fue bien, distinto de 0 si falló


def _servicios():
    """Pregunta a Docker por los contenedores y devuelve un diccionario.

    Resultado:  {"db": {...}, "backend": {...}, "frontend": {...}}
    """
    try:
        out = _compose("ps", "--format", "json")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # FileNotFoundError = no existe el comando `docker` en este equipo.
        # pytest.skip marca el test como SKIPPED: ni pasado ni fallado, sino
        # "no se pudo comprobar". IMPORTANTE: un test que no puede ejecutarse
        # jamás debe dar verde, porque sería un falso verde.
        pytest.skip("docker compose no disponible")
    if out.returncode != 0:
        pytest.skip("docker compose no disponible")

    # Detalle raro de Docker: con --format json NO devuelve un único JSON con
    # todos los contenedores, sino UN JSON POR LÍNEA, uno por contenedor.
    # Por eso hay que recorrer las líneas de una en una.
    servicios = {}
    for linea in out.stdout.splitlines():
        if not linea.strip():      # saltar líneas vacías
            continue
        try:
            # json.loads es el traductor: convierte el TEXTO en un diccionario
            # de Python de verdad, al que ya se le pueden preguntar cosas.
            info = json.loads(linea)
        except json.JSONDecodeError:
            continue               # si una línea no es JSON válido, la ignoramos
        # Guardamos cada contenedor usando su nombre de servicio como clave
        servicios[info.get("Service")] = info
    return servicios


# ══════════════════════════════════════════════════════════════════════════════
#  4 · FIXTURE — preparación compartida entre varios tests
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def client():
    """Un cliente HTTP reutilizable para los tests que solo consultan páginas.

    ESTO ES LA PARTE MÁS RARA DE PYTEST, así que léela con calma:

    Tú NUNCA llamas a client(). Lo que ocurre es que cualquier test que tenga
    UN PARÁMETRO LLAMADO `client` lo recibe automáticamente. Pytest encaja la
    fixture con el parámetro POR EL NOMBRE. Mira más abajo:

        def test_el_frontend_sirve_la_pagina_de_login(client):   ← recibe esto
                                                    ^^^^^^

    El `yield` en lugar de `return`:
        · todo lo que hay ANTES del yield se ejecuta antes del test
        · todo lo que hay DESPUÉS se ejecuta al terminar (limpieza)
    Aquí el bloque `with` cierra la conexión solo cuando acaban los tests.

    scope="module" = créalo UNA vez para todo el archivo, no uno por test.
    """
    # follow_redirects=True → si el servidor responde "ve a otra página", síguela
    # automáticamente. Cuidado: por eso los tests del login NO usan esta fixture,
    # porque necesitan ver el redirect (el código 303) sin seguirlo.
    with httpx.Client(timeout=10.0, follow_redirects=True) as c:
        yield c


# ══════════════════════════════════════════════════════════════════════════════
#  5 · TESTS ESTÁTICOS IMPRESCINDIBLES (2)
#      Leen el docker-compose.yml. Funcionan con el laboratorio APAGADO.
#      Comprueban lo que hemos PEDIDO que exista.
# ══════════════════════════════════════════════════════════════════════════════

def test_estatico_la_bd_no_declara_puertos():
    """[ESTÁTICO] IMPRESCINDIBLE 1/7 · El fichero no publica la base de datos.

    OBJETIVO
        Comprobar, sin encender nada, que en el docker-compose.yml el servicio
        `db` no tiene la clave `ports`. En Docker hay dos formas de "abrir" un
        puerto y NO son lo mismo:
            · expose → visible solo para otros contenedores (red interna)
            · ports  → PUBLICADO en tu máquina: cualquiera que te alcance, entra
        Una base de datos con `ports` es de los fallos más graves que existen.

    POSIBLES RESULTADOS
        PASSED  El diseño escrito es correcto: la BD no se publica.
        FAILED  Alguien ha añadido `ports:` al servicio db en el YAML. El
                mensaje te dice qué puertos. → bórralos: nadie de fuera la necesita

    NO PUEDE FALLAR POR
        Que el laboratorio esté apagado. Este test no lo necesita.
    """
    compose = _leer_compose()                       # Preparar: leemos el fichero
    servicio_db = compose["services"]["db"]         # Actuar: vamos al servicio db
    puertos = servicio_db.get("ports", [])          # .get da [] si la clave no existe

    assert puertos == [], (                         # Comprobar
        f"El docker-compose.yml publica la BD en {puertos}. "
        "Ningún servicio externo la necesita: quita la clave `ports` del servicio db."
    )


def test_estatico_cada_servicio_esta_en_su_red():
    """[ESTÁTICO] IMPRESCINDIBLE 2/7 · La segmentación declarada es la diseñada.

    OBJETIVO
        Comprobar que cada servicio está en las redes que le tocan Y EN NINGUNA
        MÁS. Eso último es la clave del mínimo privilegio: no basta con que
        alguien PUEDA hablar con quien necesita; hay que impedir que hable con
        todo lo demás.
        El frontend es el único que debe estar en las dos redes, porque es el
        punto de entrada: recibe al usuario por fuera y consulta la API por dentro.

    POSIBLES RESULTADOS
        PASSED  La segmentación del fichero coincide con el plan de la fase 1.
        FAILED  Algún servicio está en una red que no le corresponde, o le
                falta una. El mensaje dice cuál y qué se esperaba.
                → revisa la clave `networks:` de ese servicio

    NO PUEDE FALLAR POR
        Que el laboratorio esté apagado.
    """
    servicios = _leer_compose()["services"]

    # Recorremos el diccionario REDES_ESPERADAS que definimos arriba.
    # .items() da pares (clave, valor) → ("db", {"web_net"}), etc.
    for nombre, redes_esperadas in REDES_ESPERADAS.items():
        # set(...) convierte la lista del YAML en un conjunto, para poder
        # compararla sin que importe el orden en que estén escritas.
        redes_declaradas = set(servicios[nombre].get("networks", []))

        assert redes_declaradas == redes_esperadas, (
            f"'{nombre}' está declarado en {redes_declaradas or 'ninguna red'} "
            f"y debería estar en {redes_esperadas}"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  6 · TESTS DINÁMICOS IMPRESCINDIBLES (5)
#      Interrogan al laboratorio EN MARCHA (necesitan `make fase3-web`).
#      Comprueban lo que REALMENTE está funcionando.
# ══════════════════════════════════════════════════════════════════════════════

def test_dinamico_los_tres_servicios_estan_sanos():
    """[DINÁMICO] IMPRESCINDIBLE 3/7 · Los tres contenedores están sanos.

    OBJETIVO
        Verificar que db, backend y frontend están encendidos Y funcionando.
        No es lo mismo: un contenedor puede estar "running" con la aplicación
        de dentro caída. Va el primero a propósito, porque si esto falla todos
        los demás fallarán y sus mensajes te despistarán.

    POSIBLES RESULTADOS
        PASSED  Los tres corren, están sanos y la API responde. Puedes seguir.
        FAILED  Falta algún contenedor o está enfermo.
                → `make fase3-web` y, si insiste, `docker compose logs <nombre>`
        SKIPPED No hay Docker en este equipo, o no responde.
                → arranca Docker Desktop / el servicio docker
    """
    servicios = _servicios()                       # Preparar: preguntamos a Docker

    for nombre in ("db", "backend", "frontend"):   # Actuar: revisamos uno a uno
        info = servicios.get(nombre, {})           # .get devuelve {} si no existe

        # Comprobar 1: el contenedor está en marcha
        assert info.get("State") == "running", (
            # El !r muestra el valor "tal cual", con comillas, para distinguir
            # el texto "None" del valor vacío None. Ayuda mucho al depurar.
            f"El servicio '{nombre}' no está corriendo (estado: {info.get('State')!r}). "
            "Ejecuta: make fase3-web"
        )

        # Comprobar 2: además de encendido, está SANO.
        # Aceptamos "" porque un servicio sin healthcheck definido lo devuelve
        # vacío, y eso no debe considerarse un fallo.
        salud = info.get("Health", "")
        assert salud in ("healthy", ""), f"El servicio '{nombre}' está '{salud}'"

    # Y una comprobación de verdad, por HTTP: que la API responda.
    #
    # OJO AL CAMBIO DE LA CLASE 04. Antes esta línea preguntaba a
    # http://localhost:8000/health, es decir, al backend directamente. Al
    # cerrar ese puerto el test se puso ROJO, y estuvo bien que lo hiciera:
    # avisó de que algo que dábamos por hecho había dejado de ser cierto.
    #
    # La respuesta correcta no era reabrir el puerto, era dejar de usar un
    # atajo que ningún usuario tiene. Ahora pregunta por donde pregunta todo
    # el mundo: el 8080, a través de nginx.
    respuesta = httpx.get(f"{BACKEND_URL}/health", timeout=5)
    assert respuesta.status_code == 200


def test_dinamico_la_bd_no_esta_publicada():
    """[DINÁMICO] IMPRESCINDIBLE 4/7 · La BD no es alcanzable desde tu máquina.

    OBJETIVO
        Convertir en código la decisión de arquitectura de la fase 1. Una base
        de datos expuesta es de los fallos más graves y más comunes que existen.
        En Docker hay dos formas de "abrir" un puerto y NO son lo mismo:
            · expose → visible solo para otros contenedores (red interna)
            · ports  → PUBLICADO en tu máquina: cualquiera que te alcance, entra
        Este test comprueba que `db` no tiene lo segundo.

    ¿NO ES EL MISMO QUE EL TEST 1?
        No. El estático lee el fichero; este pregunta al contenedor que está
        corriendo AHORA. Si alguien levantó la BD a mano con `-p 5432:5432`, el
        fichero seguiría diciendo que todo va bien y solo este test lo cazaría.

    POSIBLES RESULTADOS
        PASSED  La BD solo es accesible desde la red interna. Correcto.
        FAILED  Alguien le ha puesto `ports:` al servicio db, o lo ha arrancado
                a mano con `-p 5432:5432`. El mensaje te dice qué puerto está
                abierto. → quita esa publicación: nadie de fuera la necesita
        SKIPPED No se pudo preguntar a Docker.
    """
    # Docker nos da, por contenedor, una lista "Publishers" con sus puertos.
    # Cada elemento tiene TargetPort (el de dentro) y PublishedPort (el del host).
    # PublishedPort = 0 significa "no publicado".
    publishers = _servicios().get("db", {}).get("Publishers") or []

    # Esto es una "list comprehension": se lee como
    #   "dame los elementos p de publishers que tengan un PublishedPort de verdad"
    publicados = [p for p in publishers if p.get("PublishedPort")]

    # `assert not lista` significa "la lista tiene que estar vacía".
    assert not publicados, (
        f"La BD está publicada en el host ({publicados}). "
        "Una base de datos nunca debe exponer puerto: quita `ports` del servicio db."
    )


def test_dinamico_el_frontend_sirve_la_pagina_de_login(client):
    """[DINÁMICO] IMPRESCINDIBLE 5/7 · La puerta de entrada responde y sirve el formulario.

    OBJETIVO
        Comprobar que NGINX está sirviendo la aplicación: que responde, que lo
        que devuelve es la página de login y que el formulario tiene de verdad
        un campo de contraseña (no solo un texto que lo diga).

    POSIBLES RESULTADOS
        PASSED  La web responde 200 y sirve el login. La puerta funciona.
        FAILED  Tres motivos posibles, y el mensaje te dice cuál:
                · "El frontend no responde" → nginx caído o puerto equivocado
                · "No parece la página de login" → sirve otra cosa
                · "Falta el campo de contraseña" → el HTML está incompleto

    Fíjate en el parámetro `client`: es la fixture de arriba, que pytest nos
    inyecta automáticamente por coincidir el nombre.
    """
    respuesta = client.get(FRONTEND_URL)                    # Actuar: pedimos la página

    assert respuesta.status_code == 200, "El frontend no responde"

    # .text es el HTML recibido. .lower() lo pasa a minúsculas para que la
    # comparación no dependa de mayúsculas.
    texto = respuesta.text.lower()
    assert "login" in texto or "usuario" in texto, "No parece la página de login"

    # Y que haya de verdad un campo de contraseña, no solo texto que lo diga.
    assert 'type="password"' in respuesta.text, "Falta el campo de contraseña"


def test_dinamico_el_login_correcto_lleva_al_panel():
    """[DINÁMICO] IMPRESCINDIBLE 6/7 · El flujo completo funciona de punta a punta.

    OBJETIVO
        Es el test más valioso del archivo: una sola petición atraviesa TODA la
        arquitectura —navegador → nginx → proxy /api/ → FastAPI → PostgreSQL— y
        vuelve. Si pasa, las tres piezas se están hablando entre sí.
        Comprueba tres cosas: el código 303, a dónde redirige y que entrega
        cookie de sesión.

    POSIBLES RESULTADOS
        PASSED  Login correcto, redirección al panel y sesión entregada.
        FAILED  Según el código que llegue:
                · 200 → el backend devuelve JSON en vez de redirigir; sin
                        JavaScript el navegador se queda mirando el JSON
                · 401 → la contraseña de .env no coincide con la de la BD
                        (¿cambiaste .env después de crear el volumen?)
                · 404 → el proxy /api/ de nginx no llega al backend
                · 502 → nginx está vivo pero el backend no responde

    OJO: no usa la fixture `client` a propósito. Esa fixture sigue los redirects
    automáticamente, y aquí necesitamos ver el redirect SIN seguirlo.
    """
    respuesta = httpx.post(
        f"{FRONTEND_URL}/api/login",
        # data={...} envía los campos como un formulario HTML normal
        data={"username": ADMIN_USER, "password": ADMIN_PASS},
        timeout=10,
    )

    # 303 See Other = "correcto, ahora ve a esta otra página".
    # Lo hace el servidor porque todavía no tenemos JavaScript (llega en la
    # clase 03): sin JS, el navegador se quedaría mirando la respuesta del POST.
    assert respuesta.status_code == 303, (
        f"Se esperaba 303 See Other y llegó {respuesta.status_code}. Sin redirect "
        "del servidor, el navegador se queda mirando el JSON de la API."
    )

    # La cabecera "location" dice a dónde mandar al navegador
    assert respuesta.headers.get("location") == "/panel.html"

    # Y nos ha entregado una cookie de sesión
    assert "session_id" in respuesta.cookies, "El login no entregó cookie de sesión"


def test_dinamico_el_login_incorrecto_se_rechaza():
    """[DINÁMICO] IMPRESCINDIBLE 7/7 · Una contraseña equivocada NO deja entrar.

    OBJETIVO
        Esto se llama TEST NEGATIVO, y es el que más se olvida. Sin él, la suite
        entera daría verde aunque el backend aceptase cualquier contraseña:
        todos los demás tests usan credenciales correctas y pasarían igual.
        Comprueba dos cosas: que rechaza (401) y que NO entrega sesión a quien
        no se ha autenticado.

    POSIBLES RESULTADOS
        PASSED  El login rechaza credenciales inválidas. El control funciona.
        FAILED  Es el fallo más grave que puede dar este archivo:
                · 303 o 200 → ¡la autenticación deja entrar a cualquiera!
                · 500       → el backend revienta en vez de rechazar
                · "cookie de sesión pese a fallar" → da sesión sin autenticar

    REGLA PARA LLEVARSE
        Por cada test de "esto funciona", escribe el de "esto NO funciona
        cuando no debe". Los atacantes viven en el segundo.
    """
    respuesta = httpx.post(
        f"{FRONTEND_URL}/api/login",
        data={"username": ADMIN_USER, "password": "contraseña-incorrecta"},
        timeout=10,
    )

    # 401 Unauthorized = credenciales no válidas
    assert respuesta.status_code == 401, (
        f"Con una contraseña incorrecta se esperaba 401 y llegó "
        f"{respuesta.status_code}. ¡El login estaría dejando entrar a cualquiera!"
    )

    # Y no debe entregar sesión a quien no se ha autenticado
    assert "session_id" not in respuesta.cookies, (
        "Ha entregado una cookie de sesión pese a fallar el login"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  7 · TESTS EXTRA (3, todos DINÁMICOS)
#      No comprueban que la aplicación funcione, sino que DOCUMENTAN el estado
#      inseguro de hoy. Están en verde porque el laboratorio es inseguro a
#      propósito. A partir de la clase 7 empezarán a fallar: ese fallo será la
#      señal de que el control ya funciona.
# ══════════════════════════════════════════════════════════════════════════════

def test_extra_dinamico_el_panel_es_accesible(client):
    """[DINÁMICO] EXTRA 1/3 · La página posterior al login existe y tiene su contenido.

    OBJETIVO
        Comprobar que el panel se sirve correctamente. Y de paso enseñar
        algo incómodo: se abre DIRECTAMENTE, sin haber hecho login. Hoy no hay
        control de acceso en las páginas — es OWASP A01 Broken Access Control.

    POSIBLES RESULTADOS
        PASSED  El panel responde... incluso sin sesión (hoy, a propósito).
        FAILED  · 404 → el archivo no existe o nginx no lo encuentra
                · texto distinto → alguien cambió el contenido de la página

    CUÁNDO CAMBIARÁ
        Cuando añadamos control de acceso, este test habrá que reescribirlo:
        pedirá sesión válida y comprobará que sin ella responde 401 o redirige.
    """
    respuesta = client.get(f"{FRONTEND_URL}/panel.html")
    assert respuesta.status_code == 200
    assert "<main" in respuesta.text, "El panel no trae contenido principal"


def test_extra_dinamico_la_cookie_de_sesion_es_insegura():
    """[DINÁMICO] EXTRA 2/3 · Documenta tres fallos deliberados de la cookie (OWASP A07).

    OBJETIVO
        Dejar por escrito, y verificado, el estado inseguro de hoy. La cookie:
            1.  tiene un valor predecible: "user-admin". Cualquiera lo adivina y
                se hace pasar por otro usuario.
            2.  no lleva HttpOnly → JavaScript puede leerla, un XSS la roba.
            3.  no lleva Secure   → viaja por HTTP plano; el atacante de la fase 4
                la ve en claro.

    POSIBLES RESULTADOS
        PASSED  La cookie sigue siendo insegura. Correcto HOY (clase 1).
        FAILED  ¡Buena noticia! Alguien la ha asegurado. Toca actualizar el
                test para que exija lo contrario: HttpOnly, Secure y un valor
                aleatorio e impredecible.

    CUÁNDO CAMBIARÁ
        Clase 05 (HttpOnly y valor aleatorio) y clase 07 (Secure, con HTTPS).
    """
    respuesta = httpx.post(
        f"{FRONTEND_URL}/api/login",
        data={"username": ADMIN_USER, "password": ADMIN_PASS},
        timeout=10,
    )

    # Leemos la cabecera Set-Cookie en crudo, tal y como la envía el servidor
    set_cookie = respuesta.headers.get("set-cookie", "").lower()

    assert f"session_id=user-{ADMIN_USER}" in set_cookie, "El valor debería ser predecible hoy"
    assert "httponly" not in set_cookie, "Hoy NO debería tener HttpOnly (clase 05)"
    assert "secure" not in set_cookie, "Hoy NO debería tener Secure (clase 07)"


def test_extra_dinamico_la_web_va_en_http_sin_cifrar(client):
    """[DINÁMICO] EXTRA 3/3 · Todo viaja en claro (OWASP A02 y A04).

    OBJETIVO
        Dejar constancia de la causa raíz de toda la demostración: como no hay
        cifrado, cualquiera que escuche la red lee las contraseñas. Es el
        "antes" contra el que compararemos cuando pongamos HTTPS.

    POSIBLES RESULTADOS
        PASSED  Seguimos en HTTP plano. Correcto HOY (clase 1).
        FAILED  ¡Ya hay HTTPS! Es la mejor noticia del curso: significa que el
                sniffer y el proxy de la demo ya no pueden leer nada.
                → actualiza el test para exigir "https"

    CUÁNDO CAMBIARÁ
        Clase 07, cuando pongamos TLS. Este es EL test que debe volverse rojo.
    """
    respuesta = client.get(FRONTEND_URL)
    # .url.scheme es la parte de antes de "://" → "http" o "https"
    assert respuesta.url.scheme == "http", "¿Ya hay HTTPS? Actualiza este test"

"""
═══════════════════════════════════════════════════════════════════════════════
 TESTS DE NGINX Y ARQUITECTURA — Clase 04
═══════════════════════════════════════════════════════════════════════════════

     ./.venv/bin/pytest tests/test_clase04_nginx.py -v

───────────────────────────────────────────────────────────────────────────────
 QUÉ SE COMPRUEBA AQUÍ
───────────────────────────────────────────────────────────────────────────────

 Hasta ahora los tests miraban VUESTRO código: el HTML, el CSS, el JavaScript.
 Estos miran la PUERTA: quién puede entrar, por dónde, y qué se le cuenta de
 más por el camino.

 Es la primera vez que un test del laboratorio comprueba CONFIGURACIÓN y no
 código. Y es una diferencia importante: la mayoría de las brechas reales no
 son errores de programación, son cosas mal configuradas que nadie revisó.
 Por eso A02 Security Misconfiguration lleva años entre los tres primeros del
 Top 10, y en 2025 está en el puesto 2.

───────────────────────────────────────────────────────────────────────────────
 AL EMPEZAR LA CLASE, CASI TODOS ESTÁN EN ROJO
───────────────────────────────────────────────────────────────────────────────

 Es lo normal y es la lista de tareas del laboratorio 4B. Cada paso del
 laboratorio apaga uno.
"""

# ══════════════════════════════════════════════════════════════════════════════
#  1 · IMPORTS
# ══════════════════════════════════════════════════════════════════════════════
import os
import re
import socket

import httpx
import pytest
import yaml


# ══════════════════════════════════════════════════════════════════════════════
#  2 · CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════
LAB_DIR = os.path.dirname(os.path.dirname(__file__))
COMPOSE = os.path.join(LAB_DIR, "docker-compose.yml")
NGINX_CONF = os.path.join(LAB_DIR, "nginx", "default.conf")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")
BACKEND_HOST = "localhost"
BACKEND_PORT = 8000


# ══════════════════════════════════════════════════════════════════════════════
#  3 · AYUDANTES
# ══════════════════════════════════════════════════════════════════════════════
def leer_compose():
    with open(COMPOSE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def leer_nginx():
    with open(NGINX_CONF, encoding="utf-8") as f:
        return f.read()


def sin_comentarios_nginx(conf):
    """Quita los comentarios # antes de analizar la configuración.

    Igual que en los tests de JavaScript: si no, una línea que diga
    "# aquí habría que poner server_tokens off" daría el test por bueno
    sin que la directiva exista.
    """
    return re.sub(r"#[^\n]*", "", conf)


def puerto_abierto(host, puerto, timeout=2):
    """¿Hay alguien escuchando en ese puerto de tu máquina?"""
    try:
        with socket.create_connection((host, puerto), timeout=timeout):
            return True
    except OSError:
        return False


def pedir(ruta, **kwargs):
    try:
        return httpx.get(f"{FRONTEND_URL}{ruta}", timeout=5, **kwargs)
    except httpx.RequestError:
        pytest.skip("El laboratorio no está levantado. Lanza `make fase3-web`.")


# ══════════════════════════════════════════════════════════════════════════════
#  4 · UNA SOLA PUERTA — la deuda de la clase 01
# ══════════════════════════════════════════════════════════════════════════════

def test_estatico_el_backend_no_publica_puerto():
    """[ESTÁTICO] 1 · El compose ya no publica el puerto del backend.

    OBJETIVO
        En la clase 01 declarasteis esta deuda por escrito, en el propio YAML:

            # Concesión temporal de la clase 1 (Swagger cómodo).
            # Se cierra en clase 04: es una ruta directa que evita el proxy.

        Hoy toca cerrarla. `ports:` publica el puerto en VUESTRA máquina y, si
        alguien os alcanza por red, en la suya. `expose:` lo deja visible solo
        para los otros contenedores.

        Mientras exista ese `ports:`, todo lo que configuréis en nginx —límites,
        cabeceras, registro, y el día de mañana el HTTPS— se puede saltar
        escribiendo :8000 en vez de :8080.

    POSIBLES RESULTADOS
        PASSED   El servicio backend no tiene `ports:`.
        FAILED   Sigue publicado. → quítalo del docker-compose.yml y relanza.

    OJO: este test lee el ARCHIVO. Puede estar bien escrito y seguir abierto si
    nadie ha reiniciado. Por eso hay otro dinámico justo debajo.
    """
    compose = leer_compose()
    backend = compose["services"]["backend"]

    assert "ports" not in backend, (
        "docker-compose.yml: el servicio `backend` sigue publicando puertos "
        f"({backend.get('ports')}). Esa es la ruta que evita el proxy. "
        "Quita la clave `ports:` y deja solo `expose:`."
    )


def test_dinamico_el_backend_no_es_alcanzable_sin_pasar_por_nginx():
    """[DINÁMICO] 2 · Desde tu máquina ya no se llega al backend por el 8000.

    OBJETIVO
        La comprobación de verdad. El archivo puede decir lo que quiera: lo que
        cuenta es si el puerto responde.

        Hasta hoy esto funcionaba y era un agujero:
            curl http://localhost:8000/api/documentos   → 200

        Saltarse el proxy es saltarse TODO lo que el proxy vigila. Es
        A01:2025 Broken Access Control y A02:2025 Security Misconfiguration
        a la vez.

    POSIBLES RESULTADOS
        PASSED   Nadie responde en el 8000.
        FAILED   Sigue abierto. → quita el `ports:` y `make fase3-web` otra vez.
    """
    assert not puerto_abierto(BACKEND_HOST, BACKEND_PORT), (
        f"El backend sigue respondiendo en {BACKEND_HOST}:{BACKEND_PORT}. "
        "Esa ruta evita nginx y con ella todas sus defensas. "
        "Quita `ports:` del servicio backend y relanza con `make fase3-web`."
    )


def test_dinamico_la_api_si_responde_por_la_puerta_principal():
    """[DINÁMICO] 3 · Cerrar el 8000 no debe romper la aplicación.

    OBJETIVO
        Comprobar lo contrario del test anterior, que es igual de importante:
        la API tiene que seguir funcionando POR DONDE TOCA.

        Un control de seguridad que rompe el producto no dura ni una semana:
        alguien lo quita el viernes y nadie lo vuelve a poner.

    POSIBLES RESULTADOS
        PASSED   /api/health responde 200 a través de nginx.
        FAILED   Has cerrado el 8000 pero el proxy no llega al backend.
        SKIPPED  El laboratorio está apagado.
    """
    respuesta = pedir("/api/health")

    assert respuesta.status_code == 200, (
        f"/api/health respondió {respuesta.status_code} a través del proxy. "
        "El backend tiene que seguir siendo alcanzable por nginx."
    )


def test_dinamico_la_documentacion_de_la_api_no_se_sirve_al_exterior():
    """[DINÁMICO] 4 · Swagger deja de estar a la vista.

    OBJETIVO
        FastAPI publica en /docs una interfaz que lista TODOS los endpoints,
        sus parámetros y sus respuestas. Para desarrollar es comodísimo. Para
        quien va a atacar, es el mapa del tesoro: no tiene que adivinar nada.

        Hasta hoy estaba en http://localhost:8000/docs, abierto.

        ⚠️ Matiz importante, y está en el enunciado del proyecto: Patxi OS PIDE
        que Swagger esté accesible, porque sin él no puede corregir. Eso es una
        decisión de ENTORNO de evaluación, no un descuido, y así hay que
        explicarlo en el informe. Una cosa es tenerlo abierto en un entorno de
        prácticas y otra publicarlo en producción.

    POSIBLES RESULTADOS
        PASSED   /docs no se sirve desde fuera.
        FAILED   Sigue accesible por el 8000.
    """
    if puerto_abierto(BACKEND_HOST, BACKEND_PORT):
        pytest.fail(
            f"El puerto {BACKEND_PORT} sigue abierto, así que /docs también. "
            "Cierra primero el puerto (test 1 y 2)."
        )

    # A través del proxy, /docs no está enrutado: nginx responde con la página
    # de reserva, no con Swagger.
    respuesta = pedir("/docs")
    assert "swagger" not in respuesta.text.lower(), (
        "Swagger se está sirviendo a través del proxy. Si lo necesitáis para "
        "corregir, dejadlo documentado y restringido, no abierto."
    )


# ══════════════════════════════════════════════════════════════════════════════
#  5 · LO QUE EL SERVIDOR CUENTA DE MÁS
# ══════════════════════════════════════════════════════════════════════════════

def test_estatico_nginx_declara_que_oculta_su_version():
    """[ESTÁTICO] 5 · La configuración lleva `server_tokens off`.

    OBJETIVO
        Por defecto nginx firma cada respuesta con su versión exacta:

            Server: nginx/1.27.5

        Eso no es un ataque, pero es el paso previo. Quien busca objetivos no
        prueba exploits a ciegas: filtra por versión. Decir la vuestra os mete
        en esa lista sin que nadie haya hecho nada.

        No arregla ninguna vulnerabilidad. Solo deja de regalar información,
        que es exactamente de lo que va A02.

    POSIBLES RESULTADOS
        PASSED   La directiva está escrita.
        FAILED   Falta. → añade `server_tokens off;` dentro del bloque server.
    """
    conf = sin_comentarios_nginx(leer_nginx())

    assert re.search(r"server_tokens\s+off\s*;", conf), (
        "nginx/default.conf: falta `server_tokens off;`. Sin eso, cada "
        "respuesta lleva la versión exacta del servidor."
    )


def test_dinamico_la_respuesta_no_lleva_la_version_del_servidor():
    """[DINÁMICO] 6 · Y de verdad ya no la manda.

    OBJETIVO
        Comprobar la cabecera que llega al navegador. `Server: nginx` está
        bien; `Server: nginx/1.27.5` no.

        Es la pareja del test anterior: uno mira lo ESCRITO, otro lo que
        OCURRE. Entre los dos cubren el caso de "lo configuré pero no reinicié".

    POSIBLES RESULTADOS
        PASSED   La cabecera no incluye número de versión.
        FAILED   Sigue mandándola. → reconstruye el contenedor.
        SKIPPED  El laboratorio está apagado.
    """
    respuesta = pedir("/login.html")
    server = respuesta.headers.get("server", "")

    assert not re.search(r"\d+\.\d+", server), (
        f"La respuesta sigue diciendo la versión: Server: {server!r}. "
        "Añade `server_tokens off;` y reconstruye el frontend."
    )


# ══════════════════════════════════════════════════════════════════════════════
#  6 · LÍMITES
# ══════════════════════════════════════════════════════════════════════════════

def test_estatico_nginx_limita_el_tamano_del_cuerpo():
    """[ESTÁTICO] 7 · Hay un `client_max_body_size`.

    OBJETIVO
        Sin límite, cualquiera puede enviaros un cuerpo de peticion de varios
        gigas. No hace falta ni ser listo: basta con repetirlo. El servidor se
        queda sin disco o sin memoria y la web deja de responder para todos.

        Un límite no es una molestia: es decidir tú cuánto estás dispuesto a
        aceptar, en vez de que lo decida quien os ataque.

        Y hay que ponerlo ANTES de que la petición llegue a vuestra API: para
        cuando FastAPI la mira, ya os la habéis tragado entera.

    POSIBLES RESULTADOS
        PASSED   La directiva está puesta.
        FAILED   Falta. → `client_max_body_size 2m;` en el bloque server.
    """
    conf = sin_comentarios_nginx(leer_nginx())

    assert re.search(r"client_max_body_size\s+\d+[kKmMgG]?\s*;", conf), (
        "nginx/default.conf: falta `client_max_body_size`. Sin límite, un "
        "cuerpo enorme puede tumbaros el servicio."
    )


def test_dinamico_se_aplica_el_limite_QUE_VOSOTROS_HABEIS_PUESTO():
    """[DINÁMICO] 8 · El límite que se aplica es el vuestro, no el de fábrica.

    OBJETIVO
        Aquí hay una trampa que conviene conocer: **nginx ya trae un límite de
        1 MB por defecto**. Así que un test que mande 5 MB y espere un 413
        pasaría en verde sin que nadie haya configurado nada. Un verde vacío.

        Para que el test signifique algo, lee el valor que habéis escrito en
        la configuración y comprueba DOS cosas:
          · un cuerpo por ENCIMA de vuestro límite se rechaza con 413
          · un cuerpo por DEBAJO pasa, y lo contesta la API

        Lo segundo importa tanto como lo primero: un límite tan bajo que rompa
        el producto no sirve de nada, porque alguien lo quitará el viernes.

        Y fijaos en quién responde el 413: NO es vuestra API. Es nginx, antes
        de que la petición llegue al backend. Ese es el sentido de poner los
        límites en la puerta y no dentro de casa.

    POSIBLES RESULTADOS
        PASSED   Vuestro límite se aplica, y por debajo de él la API responde.
        FAILED   El mensaje dice cuál de las dos ha fallado.
        SKIPPED  Todavía no habéis escrito `client_max_body_size`.
    """
    conf = sin_comentarios_nginx(leer_nginx())
    declarado = re.search(r"client_max_body_size\s+(\d+)\s*([kKmMgG]?)\s*;", conf)

    if not declarado:
        pytest.skip(
            "Todavía no hay `client_max_body_size` en la configuración. "
            "Comprobar el límite de fábrica de nginx sería un VERDE VACÍO: "
            "pasaría sin que hubierais hecho nada."
        )

    unidades = {"": 1, "k": 1024, "m": 1024 ** 2, "g": 1024 ** 3}
    limite = int(declarado.group(1)) * unidades[declarado.group(2).lower()]

    def enviar(tamano):
        try:
            return httpx.post(f"{FRONTEND_URL}/api/login", content=b"x" * tamano,
                              headers={"Content-Type": "application/octet-stream"},
                              timeout=20)
        except httpx.RequestError:
            pytest.skip("El laboratorio no está levantado.")

    por_encima = enviar(limite + 64 * 1024)
    assert por_encima.status_code == 413, (
        f"Vuestro límite es {limite} bytes, pero un cuerpo mayor recibió "
        f"{por_encima.status_code} en vez de 413. ¿Habéis reconstruido el "
        "frontend después de cambiar la configuración?"
    )

    por_debajo = enviar(max(1024, limite // 2))
    assert por_debajo.status_code != 413, (
        f"Un cuerpo de la mitad de vuestro límite también recibió 413. "
        "El límite está mal escrito o es demasiado pequeño: así rompéis la "
        "aplicación, y un control que rompe el producto acaba desactivado."
    )


# ══════════════════════════════════════════════════════════════════════════════
#  7 · QUÉ LE LLEGA AL BACKEND
# ══════════════════════════════════════════════════════════════════════════════

def test_estatico_nginx_reenvia_la_ruta_completa():
    """[ESTÁTICO] 9 · El `proxy_pass` de /api/ va SIN barra final.

    OBJETIVO
        Un detalle de una sola letra que cambia todo:

            proxy_pass http://backend:8000;    →  /api/documentos llega entero
            proxy_pass http://backend:8000/;   →  llega como /documentos

        Con la barra, nginx RECORTA el prefijo. Si vuestra API espera
        /api/documentos, recibe /documentos y responde 404, y pasáis media
        tarde buscando el fallo en el sitio equivocado.

    POSIBLES RESULTADOS
        PASSED   Sin barra final.
        FAILED   Con barra: el backend recibirá rutas recortadas.
    """
    conf = sin_comentarios_nginx(leer_nginx())

    bloque = re.search(r"location\s+/api/\s*\{(.*?)\}", conf, re.DOTALL)
    assert bloque, "nginx/default.conf: no encuentro el `location /api/`"

    proxy = re.search(r"proxy_pass\s+(\S+?)\s*;", bloque.group(1))
    assert proxy, "El `location /api/` no tiene `proxy_pass`"

    assert not proxy.group(1).rstrip().endswith("/"), (
        f"proxy_pass termina en barra ({proxy.group(1)}): nginx recortará el "
        "prefijo /api/ y el backend recibirá rutas que no espera."
    )


def test_dinamico_el_backend_recibe_las_cabeceras_del_proxy():
    """[DINÁMICO] 10 · X-Real-IP y X-Forwarded-For llegan al backend.

    OBJETIVO
        Cuando hay un proxy por el medio, el backend deja de ver la IP del
        usuario: ve la del proxy. Por eso nginx añade esas cabeceras.

        Miradlo con vuestros ojos en  http://localhost:8080/api/eco

        ⚠️ Y AQUÍ VIENE LA TRAMPA, que es lo importante de esta diapositiva:
        esas cabeceras las puede escribir CUALQUIERA. Si vuestra API se fía de
        X-Forwarded-For para decidir algo —permitir una IP, saltarse un
        límite—, basta con que alguien la mande a mano.

        Solo son de fiar si el backend es inalcanzable salvo a través del
        proxy. O sea: solo valen porque habéis cerrado el puerto 8000.
        Eso es A06:2025 Insecure Design.

    POSIBLES RESULTADOS
        PASSED   Las dos cabeceras llegan.
        FAILED   Falta alguna → revisa los proxy_set_header.
        SKIPPED  El laboratorio está apagado.
    """
    datos = pedir("/api/eco").json()
    cabeceras = {k.lower() for k in datos.get("cabeceras", {})}

    faltan = {"x-real-ip", "x-forwarded-for"} - cabeceras
    assert not faltan, (
        f"Al backend no le llegan estas cabeceras: {faltan}. "
        "Revisa los `proxy_set_header` del location /api/."
    )


# ══════════════════════════════════════════════════════════════════════════════
#  8 · DEJAR RASTRO
# ══════════════════════════════════════════════════════════════════════════════

def test_estatico_nginx_registra_los_accesos():
    """[ESTÁTICO] 11 · El registro de accesos está activo y nombrado.

    OBJETIVO
        Comprobar que hay un `access_log` y que NO está puesto en `off`.

        Sin registro no hay forma de saber que os han entrado, ni cuándo, ni
        por dónde. La mayoría de las brechas no se descubren por una alarma:
        se descubren semanas después mirando logs. Si no hay logs, no se
        descubren.

        Eso es A09:2025 Security Logging and Alerting Failures.

        ⚠️ Y el reverso, que también es un fallo: un log que guarde contraseñas,
        tokens o cookies es una brecha en sí mismo. Se registra QUIÉN pidió QUÉ
        y CUÁNDO, nunca el contenido.

    POSIBLES RESULTADOS
        PASSED   Hay access_log activo.
        FAILED   No hay, o está desactivado con `off`.
    """
    conf = sin_comentarios_nginx(leer_nginx())

    assert "access_log" in conf, (
        "nginx/default.conf: no hay `access_log`. Sin registro no hay forma de "
        "saber que os han entrado."
    )
    assert not re.search(r"access_log\s+off\s*;", conf), (
        "nginx/default.conf: el `access_log` está en `off`. Eso es A09."
    )


def test_dinamico_las_peticiones_quedan_registradas():
    """[DINÁMICO] 12 · Y el registro recoge de verdad lo que pasa.

    OBJETIVO
        Hacer una petición con una marca reconocible y buscarla en los logs
        del contenedor. Es la diferencia entre "configuré el log" y "el log
        funciona".

    ⚠️ ESTE YA ESTABA EN VERDE ANTES DE TOCAR NADA, Y HAY QUE DECIRLO
        nginx registra los accesos por defecto. O sea que este test pasaba
        desde la clase 01 sin que nadie hubiera decidido nada.

        Entonces, ¿para qué el test de al lado, que exige escribirlo?
        Porque «funciona por defecto» y «lo hemos decidido nosotros» no son
        lo mismo. Un valor por defecto puede cambiar al actualizar la imagen,
        o venir desactivado en otra. Lo que no está escrito, no está decidido:
        está ocurriendo por casualidad.

        Esa es también la diferencia entre los dos tests: el estático
        comprueba vuestra DECISIÓN, el dinámico comprueba el EFECTO.

    POSIBLES RESULTADOS
        PASSED   La petición aparece en los logs de nginx.
        FAILED   No aparece → el registro no está llegando a la salida.
        SKIPPED  El laboratorio está apagado, o no hay docker a mano.
    """
    import subprocess
    import uuid

    marca = f"prueba-log-{uuid.uuid4().hex[:8]}"
    pedir(f"/{marca}")

    try:
        salida = subprocess.run(
            ["docker", "compose", "logs", "--no-color", "--tail", "80", "frontend"],
            cwd=LAB_DIR, capture_output=True, text=True, timeout=25)
    except Exception:
        pytest.skip("No puedo leer los logs de docker desde aquí.")

    assert marca in salida.stdout, (
        f"La petición a /{marca} no aparece en los logs de nginx. "
        "Comprueba que `access_log` escribe a la salida estándar del contenedor."
    )

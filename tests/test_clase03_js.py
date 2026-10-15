"""
═══════════════════════════════════════════════════════════════════════════════
 TESTS DE JAVASCRIPT — Clase 03
═══════════════════════════════════════════════════════════════════════════════

 El panel deja de ser una página fija y pasa a pedirle los datos a una API.
 Eso es lo que hace útil una web, y también lo que le abre la puerta al XSS.

     ./.venv/bin/pytest tests/test_clase03_js.py -v

───────────────────────────────────────────────────────────────────────────────
 QUÉ CUBRE Y QUÉ NO
───────────────────────────────────────────────────────────────────────────────

 Cubre las SEIS vistas del proyecto y sus SIETE archivos de JavaScript.
 Cada test está escrito una vez y se ejecuta sobre todos, con parametrize.

 pytest NO tiene navegador. No puede pulsar botones, ni ejecutar vuestro
 JavaScript, ni mirar la tabla ya pintada. Así que aquí NO hay ningún test
 que diga "la tabla se rellenó bien".

 Lo que sí puede hacer, y hace:
   · leer vuestros archivos y comprobar CÓMO están escritos   → ESTÁTICO
   · llamar a los endpoints y comprobar qué devuelven         → DINÁMICO

 Para comprobar el resultado en el navegador hacen falta otras herramientas
 (Playwright, Selenium). Saber qué NO cubre tu suite es parte del oficio.
"""

# ══════════════════════════════════════════════════════════════════════════════
#  1 · IMPORTS
# ══════════════════════════════════════════════════════════════════════════════
import os
import re

import httpx
import pytest


# ══════════════════════════════════════════════════════════════════════════════
#  2 · CONSTANTES — el mapa del proyecto
# ══════════════════════════════════════════════════════════════════════════════
LAB_DIR = os.path.dirname(os.path.dirname(__file__))
FRONTEND = os.path.join(LAB_DIR, "frontend")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")

# Vistas que piden datos a la API: (página, script, endpoint, clave, es_lista)
VISTAS_API = [
    ("panel.html",    "panel.js",    "/api/documentos",  "documentos",  True),
    ("analisis.html", "analisis.js", "/api/analisis",    "analisis",    True),
    ("equipo.html",   "equipo.js",   "/api/usuarios",    "usuarios",    True),
    ("plan.html",     "plan.js",     "/api/suscripcion", "suscripcion", False),
]

# Vistas con formulario: (página, script)
VISTAS_FORMULARIO = [
    ("login.html",    "login.js"),
    ("register.html", "register.js"),
]

# Todas las vistas con su script principal
VISTAS = [(p, s) for p, s, _, _, _ in VISTAS_API] + VISTAS_FORMULARIO

# Todos los archivos de JavaScript, incluido el ayudante compartido
SCRIPTS = ["api.js"] + [s for _, s in VISTAS]


# ══════════════════════════════════════════════════════════════════════════════
#  3 · AYUDANTES
# ══════════════════════════════════════════════════════════════════════════════
def leer(ruta_relativa):
    """Devuelve el contenido de un archivo del frontend como texto."""
    ruta = os.path.join(FRONTEND, ruta_relativa)
    if not os.path.exists(ruta):
        pytest.skip(f"Todavía no existe {ruta_relativa}")
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def leer_js(nombre):
    return leer(os.path.join("js", nombre))


def sin_comentarios(js):
    """Quita los comentarios del JavaScript antes de analizarlo.

    Sin esto, un test que busque 'innerHTML' lo encontraría dentro de un
    comentario que dice "no uséis innerHTML" y daría FAILED sin motivo.
    Un test que da falsos positivos es tan dañino como uno que no detecta
    nada: al primero se le pierde la confianza, y entonces se ignoran los rojos.
    """
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.DOTALL)   # /* bloque */
    js = re.sub(r"//[^\n]*", "", js)                     # // línea
    return js


def sin_comentarios_html(html):
    """Quita los comentarios <!-- ... --> antes de analizar el HTML."""
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


# ══════════════════════════════════════════════════════════════════════════════
#  4 · DÓNDE VIVE EL JAVASCRIPT
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("pagina,script", VISTAS)
def test_estatico_el_javascript_esta_en_su_archivo(pagina, script):
    """[ESTÁTICO] 1 · Cada vista carga su JS desde un archivo externo, con defer.

    OBJETIVO
        Comprobar dos cosas en una:
          · que el <script> apunta a /js/<script> y no trae código dentro
          · que lleva `defer`

        Lo de `defer` no es estética. Sin él el script se ejecuta ANTES de que
        exista la tabla, y querySelector() devuelve null. Es el error nº 1 de
        todo el mundo la primera vez.

        Y lo del archivo externo no es manía: vuestra CSP de la clase 02
        (default-src 'self') BLOQUEA el JavaScript escrito dentro del HTML.
        Si lo ponéis inline no falla: simplemente no ocurre nada.

    POSIBLES RESULTADOS
        PASSED   Hay <script src="/js/<script>" defer></script>
        FAILED   Falta el src, falta el defer, o el JS está metido en el HTML.
    """
    html = leer(pagina)

    assert f'src="/js/{script}"' in html, (
        f'{pagina}: falta <script src="/js/{script}" defer></script>'
    )

    etiqueta = re.search(rf'<script[^>]*src="/js/{re.escape(script)}"[^>]*>', html)
    assert etiqueta and "defer" in etiqueta.group(0), (
        f"{pagina}: al <script> de {script} le falta `defer`. Sin él se ejecuta "
        "antes de que exista la página y querySelector() devuelve null."
    )


@pytest.mark.parametrize("pagina,script,endpoint,clave,es_lista", VISTAS_API)
def test_estatico_las_vistas_de_api_cargan_el_ayudante(pagina, script, endpoint, clave, es_lista):
    """[ESTÁTICO] 2 · Las vistas que hablan con la API cargan api.js, y ANTES.

    OBJETIVO
        api.js define pedirLista(), celda() y los demás ayudantes. Si se
        cargara después del script de la vista, esas funciones no existirían
        todavía y saltaría "pedirLista is not defined".

        Con `defer` los scripts se ejecutan en el ORDEN en que aparecen en el
        HTML, así que api.js tiene que ir primero. Este test comprueba el orden.

    POSIBLES RESULTADOS
        PASSED   api.js aparece antes que el script de la vista.
        FAILED   Falta api.js, o está después.
    """
    html = leer(pagina)

    assert 'src="/js/api.js"' in html, (
        f'{pagina}: falta <script src="/js/api.js" defer></script>'
    )

    pos_api = html.index('src="/js/api.js"')
    pos_vista = html.index(f'src="/js/{script}"')
    assert pos_api < pos_vista, (
        f"{pagina}: api.js se carga DESPUÉS de {script}. Con defer el orden "
        "del HTML es el orden de ejecución, así que las funciones de api.js "
        "aún no existirían."
    )


@pytest.mark.parametrize("pagina", [p for p, _ in VISTAS])
def test_estatico_no_hay_javascript_dentro_del_html(pagina):
    """[ESTÁTICO] 3 · Ningún <script> con código escrito dentro del HTML.

    OBJETIVO
        Un <script src="..."> está bien. Un <script> con código dentro, no.
        Motivo de seguridad, no de orden: para que ese código se ejecutara
        habría que añadir 'unsafe-inline' a la CSP, y en el momento en que lo
        hacéis, la CSP deja de protegeros de la inyección. Habríais desarmado
        la defensa de la clase 02 para ahorraros un archivo.

    POSIBLES RESULTADOS
        PASSED   Solo hay <script> con src.
        FAILED   Hay código suelto dentro del HTML. → sácalo a /js/
    """
    html = sin_comentarios_html(leer(pagina))

    for bloque in re.finditer(r"<script([^>]*)>(.*?)</script>", html, re.DOTALL):
        atributos, contenido = bloque.group(1), bloque.group(2).strip()
        if contenido:
            assert "src=" in atributos, (
                f"{pagina}: hay JavaScript escrito dentro del HTML:\n"
                f"   {contenido[:80]}...\n"
                "Sácalo a un archivo en /js/. Vuestra CSP lo bloquea igualmente."
            )


@pytest.mark.parametrize("pagina", [p for p, _ in VISTAS])
def test_estatico_no_hay_manejadores_de_evento_inline(pagina):
    """[ESTÁTICO] 4 · Nada de onclick=, onerror=, onsubmit= en el HTML.

    OBJETIVO
        Un manejador escrito en la etiqueta (onclick="...") es JavaScript
        inline: la CSP lo bloquea igual que a un <script> con código dentro.
        Y es la vía por la que entra un XSS, porque basta con que un dato
        acabe dentro de un atributo para que se ejecute.

        La alternativa es addEventListener(), desde vuestro archivo .js.

    POSIBLES RESULTADOS
        PASSED   No hay ningún manejador en los atributos.
        FAILED   El mensaje dice cuáles ha encontrado.
    """
    html = sin_comentarios_html(leer(pagina))

    encontrados = sorted(set(re.findall(
        r'\bon(?:click|error|load|submit|change|input|mouseover|focus|blur)\s*=',
        html, re.IGNORECASE)))

    assert not encontrados, (
        f"{pagina}: hay manejadores de evento inline {encontrados}. "
        "Son la vía principal del XSS y la CSP los bloquea. Usa addEventListener()."
    )


# ══════════════════════════════════════════════════════════════════════════════
#  5 · CÓMO HABLA CON LA API
# ══════════════════════════════════════════════════════════════════════════════

def test_estatico_el_ayudante_comprueba_que_la_respuesta_llego_bien():
    """[ESTÁTICO] 5 · api.js mira si el servidor respondió bien (res.ok).

    OBJETIVO
        fetch() NO lanza ningún error si el servidor devuelve 404 o 500.
        Esto sorprende siempre: la promesa se resuelve "con éxito", y vuestro
        código sigue adelante tan tranquilo. El fallo aparece después, al usar
        unos datos que no existen, con un mensaje que no explica nada.

        Hay que comprobarlo a mano SIEMPRE:

            const res = await fetch(ruta);
            if (!res.ok) throw new Error(`${ruta} respondió ${res.status}`);

        Esto es A10:2025 · Mishandling of Exceptional Conditions, categoría
        nueva del Top 10 de este año: el fallo no es que no haya error, es
        que el código no lo trata.

    POSIBLES RESULTADOS
        PASSED   api.js comprueba .ok (o el código de estado).
        FAILED   Se fía de que la respuesta siempre es buena.
    """
    js = sin_comentarios(leer_js("api.js"))

    assert "fetch(" in js, "api.js no llama a fetch(). ¿Es el archivo correcto?"

    # No basta con que la palabra ".ok" aparezca: tiene que estar DENTRO de una
    # condición. Si solo se menciona en el texto de un error, la comprobación
    # no existe y el test sería un verde vacío.
    guarda = re.search(r"if\s*\(\s*!\s*\w+\.ok\b", js) \
        or re.search(r"if\s*\(\s*\w+\.ok\s*(===|==)\s*false", js) \
        or re.search(r"if\s*\([^)]*\w+\.status\s*(!==|!=|>=|>)", js)

    assert guarda, (
        "api.js no comprueba si la respuesta fue correcta.\n"
        "fetch() NO falla con un 404 ni con un 500. Hace falta una condición:\n"
        "    if (!res.ok) throw new Error(...);\n"
        "Mencionar res.status solo en el mensaje de error no cuenta: eso no "
        "comprueba nada."
    )

    assert "throw" in js, (
        "api.js detecta el error pero no lo lanza. Si no se lanza, el código "
        "que llamó a la función no se entera y sigue con datos que no existen."
    )


def test_estatico_el_ayudante_comprueba_la_forma_de_la_respuesta():
    """[ESTÁTICO] 6 · api.js comprueba que los datos tienen la forma esperada.

    OBJETIVO
        Comprobar el código de estado es mirar el SOBRE. Falta mirar la CARTA.

        Si el backend renombra un campo, la respuesta sigue siendo un 200 con
        JSON válido, res.ok pasa, y el panel revienta igual con un
        "undefined is not iterable" que no dice nada útil.

            if (!Array.isArray(datos[clave])) {
              throw new Error(`${ruta} no devolvió la lista esperada`);
            }

        La regla completa son tres escalones: ¿llegó? → ¿tiene la forma?
        → ¿el contenido vale? Y es un requisito literal del proyecto de
        Programación Segura (S13): una API externa puede fallar, tardar o
        devolver basura, y vuestra web no puede caerse por eso.

    POSIBLES RESULTADOS
        PASSED   api.js valida la estructura antes de usarla.
        FAILED   Usa los datos tal cual llegan.
    """
    js = sin_comentarios(leer_js("api.js"))

    assert "Array.isArray" in js or "typeof" in js, (
        "api.js no comprueba la FORMA de lo que devuelve la API. Añade una "
        "validación tipo Array.isArray(datos[clave]) antes de devolverla."
    )


@pytest.mark.parametrize("script", SCRIPTS)
def test_estatico_ningun_script_usa_innerhtml(script):
    """[ESTÁTICO] 7 · Los datos se pintan como TEXTO, nunca como código.

    OBJETIVO
        Comprobar que no aparece innerHTML (ni outerHTML, ni document.write)
        en ninguno de vuestros archivos.

            elemento.textContent = dato;   ✅ escribe TEXTO
            elemento.innerHTML   = dato;   ❌ escribe CÓDIGO

        No es cuestión de comodidad: son dos operaciones distintas. Con
        innerHTML, un nombre de documento que sea <img src=x onerror="...">
        deja de ser un nombre y pasa a ser una orden.

        Y fijaos de dónde viene el ataque: no de vuestro código, sino de un
        DATO guardado en la base de datos. El atacante no toca vuestro
        JavaScript, solo espera a que alguien lo pinte.

        Esto es A05:2025 · Injection, donde vive el XSS desde 2021.

    POSIBLES RESULTADOS
        PASSED   No se usa ningún sink peligroso.
        FAILED   El mensaje dice cuál y en qué archivo.
    """
    js = sin_comentarios(leer_js(script))

    peligrosos = [s for s in ("innerHTML", "outerHTML", "document.write", "eval(")
                  if s in js]

    assert not peligrosos, (
        f"js/{script} usa {peligrosos} con datos que pueden venir de fuera.\n"
        "Un nombre de documento puede traer <img src=x onerror=...>: con "
        "innerHTML eso se ejecuta.\n"
        "Usa textContent o createElement(), que escriben texto y nunca lo interpretan."
    )


@pytest.mark.parametrize("script", SCRIPTS)
def test_estatico_ningun_script_contiene_secretos(script):
    """[ESTÁTICO] 8 · Ninguna credencial escrita en el código del navegador.

    OBJETIVO
        Todo lo que llega al navegador es público. No hay excepciones, ni
        ofuscación que valga: cualquiera abre F12 y lo lee. Una contraseña,
        una clave de API o un token escritos aquí están regalados.

        Es lo que evalúa literalmente el enunciado del proyecto final:
        «Secretos: que no haya ninguno. Todo lo que llega al navegador es
        público».

    POSIBLES RESULTADOS
        PASSED   No hay nada que parezca una credencial.
        FAILED   El mensaje dice qué ha encontrado.
    """
    js = sin_comentarios(leer_js(script))

    sospechosos = [
        r'password\s*[:=]\s*["\']',
        r'passwd\s*[:=]\s*["\']',
        r'api_?key\s*[:=]\s*["\']',
        r'secret\s*[:=]\s*["\']',
        r'token\s*[:=]\s*["\'][^"\']{8,}',
    ]
    for patron in sospechosos:
        encontrado = re.search(patron, js, re.IGNORECASE)
        assert not encontrado, (
            f"js/{script} parece contener una credencial: {encontrado.group(0)!r}\n"
            "Todo lo que llega al navegador es público. Eso va en el servidor."
        )


# ══════════════════════════════════════════════════════════════════════════════
#  6 · LOS FORMULARIOS
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("pagina,script", VISTAS_FORMULARIO)
def test_estatico_el_formulario_se_conecta_con_addeventlistener(pagina, script):
    """[ESTÁTICO] 9 · El envío se intercepta con addEventListener, no con onsubmit.

    OBJETIVO
        Comprobar las dos piezas que hacen falta para avisar al usuario:
          · addEventListener("submit", ...) para enterarse del envío
          · preventDefault() para PARARLO si hay errores

        Sin preventDefault() el navegador envía el formulario y recarga la
        página, y los mensajes que acabáis de pintar desaparecen al instante.

    POSIBLES RESULTADOS
        PASSED   Usa addEventListener y preventDefault.
        FAILED   El mensaje dice cuál de los dos falta.
    """
    js = sin_comentarios(leer_js(script))

    assert 'addEventListener("submit"' in js.replace("'", '"'), (
        f"js/{script}: no intercepta el envío con "
        'addEventListener("submit", ...)'
    )
    assert "preventDefault()" in js, (
        f"js/{script}: falta evento.preventDefault(). Sin él la página se "
        "recarga y vuestros mensajes desaparecen."
    )


@pytest.mark.parametrize("pagina,script", VISTAS_FORMULARIO)
def test_estatico_los_formularios_llevan_novalidate(pagina, script):
    """[ESTÁTICO] 10 · El <form> lleva novalidate para que vuestro JS se ejecute.

    OBJETIVO
        Si el formulario NO lleva novalidate, el `required` del navegador se
        dispara primero, bloquea el envío con su propio mensaje en inglés, y
        el evento `submit` nunca llega a ocurrir: vuestro JavaScript no se
        ejecuta jamás.

        novalidate significa «navegador, los mensajes los pongo yo».

        ⚠️ Y tiene un precio, que conviene saber: los `required` siguen
        escritos, pero desactivados. Si el usuario apaga JavaScript, no queda
        ninguna comprobación. Da igual: la que protege es la del servidor.

    POSIBLES RESULTADOS
        PASSED   El <form> lleva novalidate.
        FAILED   No lo lleva, y vuestra validación no se ejecutará nunca.
    """
    html = leer(pagina)

    formulario = re.search(r"<form[^>]*>", html)
    assert formulario, f"{pagina}: no encuentro ningún <form>"
    assert "novalidate" in formulario.group(0), (
        f"{pagina}: al <form> le falta novalidate. Sin él, el required del "
        "navegador se dispara antes y vuestro JavaScript no se ejecuta nunca."
    )


def test_estatico_la_fuerza_de_la_clave_se_exige_al_registrarse_y_no_al_entrar():
    """[ESTÁTICO] 11 · Las reglas de contraseña van en el registro, no en el login.

    OBJETIVO
        Dejar verificado dónde va cada comprobación:

          · En el REGISTRO se ELIGE la contraseña  → ahí sí se exige que sea
            fuerte: es el único momento en que podéis influir en ella.
          · En el LOGIN la contraseña YA EXISTE    → ahí solo se comprueba que
            no esté vacía. Si es la correcta o no, lo dice el servidor.

        Y hay un motivo de seguridad, no solo de comodidad: exigir el formato
        en el login REGALA vuestra política de contraseñas a cualquiera que
        abra la página, sin tener ni que registrarse.

    POSIBLES RESULTADOS
        PASSED   register.js exige fuerza; login.js no la aplica al enviar.
        FAILED   O falta en el registro, o sobra en el login.
    """
    registro = sin_comentarios(leer_js("register.js"))
    login = sin_comentarios(leer_js("login.js"))

    assert "loQueFaltaEnLaClave" in registro, (
        "register.js no comprueba la fuerza de la contraseña. Ahí es donde toca."
    )
    assert re.search(r"[A-Z]", registro) and "push(" in registro, (
        "register.js: la comprobación de fuerza no parece completa."
    )

    # En el login la función puede estar definida (se la llevan al registro),
    # pero NO debe usarse dentro del manejador de envío.
    manejador = login.split('addEventListener("submit"', 1)
    if len(manejador) > 1:
        assert "loQueFaltaEnLaClave(" not in manejador[1], (
            "login.js exige una contraseña fuerte al entrar. Eso bloquea a quien "
            "ya tiene una contraseña antigua y regala vuestra política de "
            "contraseñas. Déjalo solo en el registro."
        )


# ══════════════════════════════════════════════════════════════════════════════
#  7 · LOS DINÁMICOS — los endpoints de verdad
# ══════════════════════════════════════════════════════════════════════════════

def _pedir(ruta):
    try:
        respuesta = httpx.get(f"{FRONTEND_URL}{ruta}", timeout=5)
    except httpx.RequestError:
        pytest.skip("El laboratorio no está levantado. Lanza `make fase3-web`.")
    return respuesta


@pytest.mark.parametrize("pagina,script,endpoint,clave,es_lista", VISTAS_API)
def test_dinamico_cada_endpoint_responde_con_la_forma_acordada(
        pagina, script, endpoint, clave, es_lista):
    """[DINÁMICO] 12 · Cada endpoint devuelve lo que su vista espera.

    OBJETIVO
        Un frontend y un backend se ponen de acuerdo en una FORMA. Si el
        backend cambia "documentos" por "items" un martes, la vista deja de
        funcionar y nadie sabe por qué. Este test es ese acuerdo, escrito.

        Es la versión pequeña de lo que en el proyecto será la especificación
        OpenAPI (F10 del enunciado de Artxibo).

    POSIBLES RESULTADOS
        PASSED   Responde 200 y trae la clave con el tipo correcto.
        FAILED   El mensaje dice qué falla.
        SKIPPED  El laboratorio está apagado.
    """
    respuesta = _pedir(endpoint)

    assert respuesta.status_code == 200, (
        f"{endpoint} respondió {respuesta.status_code} en vez de 200"
    )
    assert "application/json" in respuesta.headers.get("content-type", ""), (
        f"{endpoint} no devuelve JSON. ¿Está llegando al backend o lo está "
        "atendiendo nginx con la página de reserva?"
    )

    datos = respuesta.json()
    assert clave in datos, f"{endpoint}: la respuesta no trae la clave '{clave}'"

    if es_lista:
        assert isinstance(datos[clave], list), f"{endpoint}: '{clave}' no es una lista"
        assert datos[clave], f"{endpoint}: '{clave}' está vacía"
    else:
        assert isinstance(datos[clave], dict), f"{endpoint}: '{clave}' no es un objeto"


def test_dinamico_los_documentos_traen_todos_sus_campos():
    """[DINÁMICO] 13 · Cada documento trae los cinco campos que pinta la tabla.

    OBJETIVO
        La vista escribe doc.nombre, doc.tamano_kb, doc.subido y doc.estado.
        Si el backend deja de mandar uno, la celda saldría vacía sin avisar.

    POSIBLES RESULTADOS
        PASSED   Todos los documentos tienen los cinco campos.
        FAILED   El mensaje dice a qué documento le falta cuál.
        SKIPPED  El laboratorio está apagado.
    """
    datos = _pedir("/api/documentos").json()
    campos = {"id", "nombre", "tamano_kb", "subido", "estado"}

    for doc in datos["documentos"]:
        faltan = campos - set(doc)
        assert not faltan, f"Al documento {doc.get('id')} le faltan: {faltan}"


def test_dinamico_los_usuarios_traen_todos_sus_campos():
    """[DINÁMICO] 14 · Cada usuario trae los campos que pinta la vista de equipo.

    POSIBLES RESULTADOS
        PASSED   Todos los usuarios tienen los seis campos.
        FAILED   El mensaje dice a quién le falta cuál.
        SKIPPED  El laboratorio está apagado.
    """
    datos = _pedir("/api/usuarios").json()
    campos = {"id", "nombre", "correo", "rol", "alta", "estado"}

    for u in datos["usuarios"]:
        faltan = campos - set(u)
        assert not faltan, f"Al usuario {u.get('id')} le faltan: {faltan}"


def test_dinamico_todos_los_usuarios_son_admin_deuda_declarada():
    """[DINÁMICO] 15 · Hoy TODO el mundo es admin, y está escrito que lo es.

    OBJETIVO
        Este test está en VERDE porque el laboratorio es inseguro, igual que
        los de la clase 01. Documenta una deuda, no una virtud.

        Un panel donde cualquiera administra a cualquiera es A01:2025 Broken
        Access Control de manual. Está así a propósito porque los roles son
        materia de la clase 06: hasta que no haya sesiones de verdad (clase 05)
        no se puede saber quién es quién.

        A partir de la clase 06 este test tendrá que FALLAR, y ese fallo será
        la prueba de que los roles existen. Cuando llegue ese día, se cambia
        por su contrario.

    POSIBLES RESULTADOS
        PASSED   Siguen siendo todos admin (hoy, a propósito).
        FAILED   Alguien ya tiene otro rol → toca reescribir este test.
        SKIPPED  El laboratorio está apagado.
    """
    datos = _pedir("/api/usuarios").json()
    roles = {u["rol"] for u in datos["usuarios"]}

    assert roles == {"admin"}, (
        f"Los roles ya no son todos admin: {roles}. Si esto es porque habéis "
        "implementado roles de verdad, enhorabuena: reescribid este test para "
        "que compruebe lo contrario."
    )


def test_dinamico_el_aviso_de_la_deuda_esta_visible_en_la_pagina():
    """[DINÁMICO] 16 · La vista de equipo avisa de que todos son admin.

    OBJETIVO
        Un fallo conocido y escrito no es lo mismo que un fallo escondido.
        La vista lleva un aviso visible que dice qué está mal, qué categoría
        de OWASP es y en qué clase se arregla.

        Esto importa para la auditoría cruzada del proyecto: un hallazgo que
        el equipo ya ha documentado se valora distinto de uno que ha ocultado.

    POSIBLES RESULTADOS
        PASSED   El aviso está en la página servida.
        FAILED   Se ha quitado el aviso y la deuda ha quedado escondida.
        SKIPPED  El laboratorio está apagado.
    """
    html = _pedir("/equipo.html").text

    assert "A01" in html and "Broken Access Control" in html, (
        "equipo.html ya no avisa de que todos son admin. Si se deja sin avisar, "
        "la deuda pasa de declarada a escondida."
    )


def test_dinamico_la_api_sirve_el_nombre_peligroso_sin_tocarlo():
    """[DINÁMICO] 17 · La API devuelve el nombre malicioso tal cual lo guardó.

    OBJETIVO
        Dejar documentado, y verificado, DE DÓNDE viene el peligro.

        La API guarda un nombre de documento que contiene una etiqueta
        <img ... onerror=...> y lo devuelve sin modificar.

        Y está bien que lo devuelva sin modificar: el servidor no sabe si ese
        texto acabará en un HTML, en un PDF o en un correo. Quien decide cómo
        se escribe es quien lo pinta. Por eso la defensa del XSS está en el
        frontend, en el momento de pintar, y se llama textContent.

    POSIBLES RESULTADOS
        PASSED   La API devuelve el nombre peligroso intacto (hoy, a propósito).
        FAILED   Alguien lo filtró en el servidor. → revisar el guion de clase.
        SKIPPED  El laboratorio está apagado.
    """
    datos = _pedir("/api/documentos").json()
    nombres = [d["nombre"] for d in datos["documentos"]]
    peligrosos = [n for n in nombres if "<img" in n.lower() and "onerror" in n.lower()]

    assert peligrosos, (
        "La API ya no devuelve el documento con el nombre malicioso. Sin él no "
        "se puede hacer la demostración de XSS de la clase."
    )


@pytest.mark.parametrize("pagina", [p for p, _ in VISTAS])
def test_dinamico_cada_vista_se_sirve_como_html(pagina):
    """[DINÁMICO] 18 · Las seis vistas existen de verdad en el servidor.

    OBJETIVO
        Comprobar que cada página responde 200 y que es HTML.

        El matiz importante: este nginx tiene `try_files ... /login.html`, así
        que una ruta que NO existe también responde 200, pero devolviendo el
        login. Por eso no basta con mirar el código: hay que comprobar que el
        contenido es el de esa página.

        Lección suelta y valiosa: un 200 no significa que exista lo que pediste.

    POSIBLES RESULTADOS
        PASSED   La página existe y es la suya.
        FAILED   Falta el archivo y nginx está sirviendo el login en su lugar.
        SKIPPED  El laboratorio está apagado.
    """
    respuesta = _pedir(f"/{pagina}")

    assert respuesta.status_code == 200, f"/{pagina} respondió {respuesta.status_code}"
    assert "text/html" in respuesta.headers.get("content-type", "")

    esperado = pagina.replace(".html", "")
    marcas = {
        "login":    "Acceso al laboratorio",
        "register": "Crear cuenta",
        "panel":    "tabla-documentos",
        "analisis": "tabla-analisis",
        "equipo":   "tabla-equipo",
        "plan":     "Consumo del mes",
    }
    assert marcas[esperado] in respuesta.text, (
        f"/{pagina} responde 200 pero el contenido no es el suyo. Seguramente "
        "el archivo no existe y nginx está sirviendo login.html como reserva."
    )

"""
═══════════════════════════════════════════════════════════════════════════════
 TESTS DE HTML Y CSS — Clase 02
═══════════════════════════════════════════════════════════════════════════════

 Estos los escribimos JUNTOS en clase. En la tarea los ampliaréis vosotros.

     ./.venv/bin/pytest tests/test_clase02_html_css.py -v

───────────────────────────────────────────────────────────────────────────────
 LO NUEVO DE ESTE ARCHIVO: casi todos son ESTÁTICOS
───────────────────────────────────────────────────────────────────────────────

 En la clase 01 casi todos los tests eran DINÁMICOS: había que levantar Docker,
 preguntar a los contenedores, hacer peticiones HTTP.

 Aquí no. Comprobar si tu HTML tiene un <main>, si cada campo tiene su etiqueta
 o si te has dejado un onclick= suelto es LEER UN ARCHIVO DE TEXTO. No hace
 falta levantar nada:

     make down                                        ← laboratorio apagado
     ./.venv/bin/pytest tests/test_clase02_html_css.py -v   ← y funcionan igual

 Eso es exactamente lo que hacen HTMLHint y axe dentro de VS Code mientras
 escribís, y lo que hace un SAST en la tubería DevSecOps: analizar el código
 fuente SIN ejecutarlo. Es el análisis más barato que existe, y por eso es el
 primero de la tubería.

 Solo hay un test DINÁMICO al final, y está ahí para enseñar algo que los
 estáticos NO pueden ver.
"""

# ══════════════════════════════════════════════════════════════════════════════
#  1 · IMPORTS
# ══════════════════════════════════════════════════════════════════════════════
import os
import re          # expresiones regulares: buscar patrones dentro de un texto

import httpx       # solo lo usa el último test, el dinámico
import pytest


# ══════════════════════════════════════════════════════════════════════════════
#  2 · CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════
LAB_DIR = os.path.dirname(os.path.dirname(__file__))
FRONTEND = os.path.join(LAB_DIR, "frontend")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")

# Las páginas que tienen que cumplir todo esto.
# Cuando creéis register.html o mi-panel.html, añadidlas aquí:
# los tests ya escritos se les aplicarán solos.
PAGINAS = [
    "login.html",
    "register.html",
    "panel.html",
    "analisis.html",
    "equipo.html",
    "plan.html",
]


# ══════════════════════════════════════════════════════════════════════════════
#  3 · AYUDANTE
# ══════════════════════════════════════════════════════════════════════════════
def leer(pagina):
    """Devuelve el contenido de una página del frontend como texto.

    Esto es TODO lo que necesita un test estático: abrir un archivo y leerlo.
    Compáralo con la fontanería de docker del archivo de la clase 01.
    """
    ruta = os.path.join(FRONTEND, pagina)
    if not os.path.exists(ruta):
        pytest.skip(f"Todavía no existe {pagina}")
    with open(ruta, encoding="utf-8") as f:
        return f.read()


# ══════════════════════════════════════════════════════════════════════════════
#  4 · BLOQUE A — ESTRUCTURA SEMÁNTICA
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("pagina", PAGINAS)
def test_estatico_el_idioma_esta_declarado(pagina):
    """[ESTÁTICO] A1 · Cada página declara que está en español.

    OBJETIVO
        Comprobar que existe <html lang="es">. El atajo html:5 de VS Code genera
        lang="en" por defecto, y casi todo el mundo se lo deja puesto.
        No es una manía: un lector de pantalla usa ese atributo para elegir la
        voz. Con lang="en" lee el español con acento inglés y no se entiende.
        Es el criterio 3.1.1 de las WCAG.

    POSIBLES RESULTADOS
        PASSED   La página declara su idioma correctamente.
        FAILED   Falta el atributo, o sigue puesto "en". → cámbialo a lang="es"
        SKIPPED  Esa página todavía no existe (normal con register.html).

    OJO: @pytest.mark.parametrize ejecuta este MISMO test una vez por cada
    página de la lista PAGINAS. Un test escrito, dos (o tres) comprobaciones.
    """
    html = leer(pagina)
    assert '<html lang="es"' in html, (
        f"{pagina}: falta <html lang=\"es\">. El atajo html:5 pone lang=\"en\": cámbialo."
    )


@pytest.mark.parametrize("pagina", PAGINAS)
def test_estatico_hay_estructura_semantica(pagina):
    """[ESTÁTICO] A2 · La página usa <main>, no solo <div>.

    OBJETIVO
        <main> le dice al navegador y al lector de pantalla dónde empieza el
        contenido de verdad. Sin él, quien navega con teclado tiene que pasar
        por el menú entero en cada página.
        Y para nosotros hay un motivo extra: un HTML con estructura clara es un
        HTML más fácil de auditar. Una web hecha solo de <div> anidados esconde
        los errores.

    POSIBLES RESULTADOS
        PASSED   Hay una etiqueta <main>.
        FAILED   No la hay. → envuelve el contenido principal en <main>...</main>
    """
    html = leer(pagina)
    assert "<main>" in html or "<main " in html, (
        f"{pagina}: no encuentro <main>. Envuelve el contenido principal en <main>."
    )


def test_estatico_cada_campo_tiene_su_etiqueta():
    """[ESTÁTICO] A3 · Cada <input> del login tiene una <label> asociada.

    OBJETIVO
        Asociada de verdad: el atributo for de la etiqueta debe coincidir con el
        id del campo. Si solo hay un placeholder, el texto desaparece en cuanto
        el usuario escribe, y un lector de pantalla no anuncia nada.
        En seguridad esto importa más de lo que parece: un formulario donde no
        se ve claro qué se está pidiendo es la base del phishing de interfaz.

    POSIBLES RESULTADOS
        PASSED   Todos los campos con id tienen su label apuntando a ese id.
        FAILED   El mensaje te dice QUÉ id se ha quedado sin etiqueta.
    """
    html = leer("login.html")

    # re.findall busca TODAS las coincidencias del patrón y devuelve una lista.
    #   id="([a-z]+)"  → captura lo que haya dentro de las comillas
    ids_de_campos = re.findall(r'<input[^>]*id="([^"]+)"', html)
    fors_de_labels = re.findall(r'<label[^>]*for="([^"]+)"', html)

    assert ids_de_campos, "login.html: no encuentro ningún <input> con id"

    for campo in ids_de_campos:
        assert campo in fors_de_labels, (
            f"El campo id=\"{campo}\" no tiene <label for=\"{campo}\">. "
            "Un placeholder NO es una etiqueta."
        )


# ══════════════════════════════════════════════════════════════════════════════
#  5 · BLOQUE B — VALIDACIÓN NATIVA
# ══════════════════════════════════════════════════════════════════════════════

def test_estatico_el_formulario_valida_en_el_navegador():
    """[ESTÁTICO] B1 · El formulario usa la validación que trae HTML de serie.

    OBJETIVO
        required y autocomplete son gratis: los escribes y el navegador hace el
        trabajo, sin una línea de JavaScript. Es la primera línea de defensa.

        ⚠️ Y AQUÍ LA ADVERTENCIA MÁS IMPORTANTE DE LA CLASE:
        esto es COMODIDAD, no seguridad. Cualquiera abre las herramientas de
        desarrollo, borra el atributo required y envía lo que quiera. O usa curl
        directamente y se salta el formulario entero.
        La validación de verdad es SIEMPRE la del servidor. Esta solo evita que
        un usuario honesto se equivoque.

    POSIBLES RESULTADOS
        PASSED   Los campos llevan required y autocomplete.
        FAILED   Falta alguno. El mensaje dice cuál.
    """
    html = leer("login.html")

    assert html.count("required") >= 2, (
        "Los dos campos del login deberían llevar 'required'"
    )
    assert 'autocomplete="username"' in html, (
        "Falta autocomplete=\"username\": ayuda al gestor de contraseñas a "
        "rellenar el campo correcto, y eso previene phishing"
    )
    assert 'autocomplete="current-password"' in html, (
        "Falta autocomplete=\"current-password\" en el campo de contraseña"
    )


def test_estatico_la_contrasena_no_se_ve_al_escribirla():
    """[ESTÁTICO] B2 · El campo de contraseña es type="password".

    OBJETIVO
        Parece una obviedad, y es de los fallos más frecuentes al copiar y pegar
        un campo: se queda como type="text" y la contraseña se ve en pantalla,
        se guarda en el historial del formulario y sale en las capturas.

    POSIBLES RESULTADOS
        PASSED   Existe un campo type="password".
        FAILED   No lo hay. → ponle type="password" al campo de contraseña
    """
    html = leer("login.html")
    assert 'type="password"' in html, (
        "login.html: el campo de contraseña debe ser type=\"password\""
    )


# ══════════════════════════════════════════════════════════════════════════════
#  6 · BLOQUE C — HTML SEGURO: LO QUE NO DEBE ESTAR
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("pagina", PAGINAS)
def test_estatico_sin_manejadores_de_eventos_inline(pagina):
    """[ESTÁTICO] C1 · Ni un solo onclick=, onerror=, onload=... en el HTML.

    OBJETIVO
        Un manejador inline es JavaScript escrito dentro de una etiqueta:
            <button onclick="borrarTodo()">
        Dos motivos para desterrarlos:
          1. Son el vehículo habitual del XSS. El payload más usado del mundo es
             <img src=x onerror="...">: no necesita ni la etiqueta <script>.
          2. Hacen IMPOSIBLE aplicar una CSP decente. Una política que permita
             scripts inline ('unsafe-inline') no protege de nada.
        Es decir: si quieres CSP, primero tienes que limpiar esto.

    POSIBLES RESULTADOS
        PASSED   El HTML está limpio.
        FAILED   El mensaje te dice exactamente qué manejador y en qué página.
                 → sácalo a un archivo .js con addEventListener (clase 03)
    """
    html = leer(pagina)

    # \bon[a-z]+\s*=  →  "on" seguido de letras y un igual: onclick=, onerror=...
    # \b es "principio de palabra", para no confundirnos con palabras que
    # terminen en "on" (por ejemplo, un atributo llamado "button=").
    encontrados = re.findall(r'\bon[a-z]+\s*=', html, re.IGNORECASE)

    assert not encontrados, (
        f"{pagina}: hay manejadores de eventos inline {set(encontrados)}. "
        "Son la vía principal del XSS y bloquean cualquier CSP seria."
    )


@pytest.mark.parametrize("pagina", PAGINAS)
def test_estatico_los_metadatos_de_seguridad_estan_puestos(pagina):
    """[ESTÁTICO] C2 · Están los metadatos que SÍ hacen algo.

    OBJETIVO
        Comprobar los cuatro que funcionan de verdad:
          · charset      → que el navegador no tenga que adivinar la codificación
          · description  → genérica, sin revelar la arquitectura
          · robots       → una pantalla de acceso no se indexa
          · referrer     → no filtrar nuestra URL a terceros al salir

    POSIBLES RESULTADOS
        PASSED   Los cuatro están presentes.
        FAILED   El mensaje dice cuál falta.

    FÍJATE EN LO QUE ESTE TEST *NO* COMPRUEBA
        No comprueba X-Frame-Options. A propósito. Ese metadato está en las
        páginas, pero no hace absolutamente nada (lo visteis en el iframe).
        Un test que comprobara "está el meta" estaría en verde certificando una
        protección que no existe. Eso es un FALSO VERDE, y es peor que no tener
        test. Lo correcto se comprueba en la clase 08, sobre la cabecera HTTP.
    """
    html = leer(pagina)

    obligatorios = {
        "charset": r'<meta\s+charset=',
        "description": r'<meta\s+name="description"',
        "robots": r'<meta\s+name="robots"',
        "referrer": r'<meta\s+name="referrer"',
    }

    for nombre, patron in obligatorios.items():
        assert re.search(patron, html, re.IGNORECASE), (
            f"{pagina}: falta el metadato '{nombre}'"
        )


def test_estatico_la_hoja_de_estilos_es_externa():
    """[ESTÁTICO] C3 · El CSS va en su archivo, no dentro del HTML.

    OBJETIVO
        Tres razones, y las tres importan:
          1. Seguridad: los estilos inline (style="...") y los bloques <style>
             obligan a relajar la CSP igual que los scripts inline.
          2. Mantenimiento: un cambio de color en un sitio, no en catorce.
          3. Rendimiento: el navegador cachea el .css una vez para toda la web.

    POSIBLES RESULTADOS
        PASSED   Hay un <link rel="stylesheet"> y ningún style= suelto.
        FAILED   O falta la hoja externa, o hay estilos incrustados en el HTML.
    """
    html = leer("login.html")

    assert 'rel="stylesheet"' in html, (
        "login.html: los estilos deben ir en un archivo aparte, "
        "enlazado con <link rel=\"stylesheet\" href=\"/css/base.css\">"
    )
    assert "style=" not in html, (
        "login.html: hay estilos inline (style=\"...\"). Sácalos al archivo CSS."
    )


# ══════════════════════════════════════════════════════════════════════════════
#  7 · EL ÚNICO DINÁMICO — y está aquí por un motivo
# ══════════════════════════════════════════════════════════════════════════════

def test_dinamico_el_meta_no_se_convierte_en_cabecera():
    """[DINÁMICO] D1 · Demuestra POR QUÉ X-Frame-Options no protege.

    OBJETIVO
        Este es el test que un estático NO puede escribir, y por eso existe:
        · Leyendo el archivo, el <meta http-equiv="X-Frame-Options"> ESTÁ ahí.
        · Pidiendo la página por HTTP, la cabecera NO llega.
        El metadato existe en el documento y no se convierte en cabecera. Y el
        navegador solo obedece a X-Frame-Options cuando viene como cabecera.
        Conclusión: escribirlo en el HTML no protege de nada.

        Esta es la diferencia entre estático y dinámico en una frase:
        el estático ve lo que ESTÁ ESCRITO, el dinámico ve lo que OCURRE.

    POSIBLES RESULTADOS
        PASSED   Confirmado: el meta está en el HTML y no llega como cabecera.
                 (Hoy es lo correcto: la cabecera se añade en la CLASE 08.)
        FAILED   ¡Ya hay cabecera! Alguien la ha puesto en NGINX. Enhorabuena:
                 actualizad este test, porque la protección ya es real.
        SKIPPED  El laboratorio no está levantado. → make fase3-web
    """
    # Preparar: leer el archivo (estático) y pedir la página (dinámico)
    html_en_disco = leer("login.html")
    try:
        respuesta = httpx.get(f"{FRONTEND_URL}/login.html", timeout=5)
    except httpx.RequestError:
        pytest.skip("Laboratorio no levantado. Ejecuta: make fase3-web")

    # 1. El metadato SÍ está escrito en el documento
    assert "X-Frame-Options" in html_en_disco, (
        "Para esta demostración, login.html debe llevar el <meta> de X-Frame-Options"
    )

    # 2. ...y sin embargo NO llega como cabecera HTTP
    cabeceras = {k.lower() for k in respuesta.headers}
    assert "x-frame-options" not in cabeceras, (
        "¡Ahora SÍ llega la cabecera X-Frame-Options! Si la habéis añadido en "
        "NGINX, la protección ya es real: actualizad este test."
    )

# TAREA CLASE 02 — Amplía los tests de HTML y CSS

**Entrega:** `tests/test_clase02_html_css.py` ampliado, en tu repositorio
**Se corrige al empezar la clase 03**
**No necesitas levantar Docker:** casi todos son estáticos

---

## Lo que ya tienes hecho

En clase escribimos juntos **13 tests**. Ejecútalos y míralos por dentro:

```bash
./.venv/bin/pytest tests/test_clase02_html_css.py -v
```

Están divididos en tres bloques, y son tu plantilla:

| Bloque | Qué comprueba | Tests ya hechos |
|--------|---------------|-----------------|
| **A** · Estructura semántica | `lang="es"`, `<main>`, `<label for=>` | 5 |
| **B** · Validación nativa | `required`, `autocomplete`, `type="password"` | 2 |
| **C** · HTML seguro | Sin `onclick=`, metadatos, CSS externo | 5 |
| **D** · El dinámico | El `<meta>` no llega como cabecera | 1 |

> 💡 **Prueba esto antes de empezar:** `make down` y vuelve a ejecutarlos.
> 12 siguen pasando con el laboratorio **apagado**. Eso es un test estático:
> leer un archivo de texto. Es lo más barato que existe, y por eso va primero
> en la tubería DevSecOps.

---

## Lo que tienes que añadir: mínimo 6 tests

### Bloque A — Estructura semántica (mínimo 2)

- **La jerarquía de títulos no se salta niveles.** Debe ir `h1 → h2 → h3`, nunca
  `h1 → h3`. Un lector de pantalla construye el índice de la página con eso.
  *Pista:* `re.findall(r'<h([1-6])', html)` te da la lista de niveles en orden.
- **Hay un solo `<h1>` por página.** Es el título de la página, no un tamaño de
  letra.
- **Ninguna imagen sin `alt`.** Si hay `<img>`, tiene que llevar texto
  alternativo. Sin él, quien no ve la imagen no se entera de nada.

### Bloque B — Validación nativa (mínimo 2)

- **El campo de contraseña tiene `minlength`.** Y piensa qué valor: ¿por qué 8 y
  no 4?
- **`register.html` valida igual que el login.** La página de registro (la que
  en clase llamamos «LogUp») no puede pedir menos requisitos que el login.
- **El campo de correo es `type="email"`.** El navegador valida el formato solo.

> ⚠️ **Y escribe en el docstring por qué esto NO es seguridad.** Cualquiera abre
> las herramientas de desarrollo, borra el `required` y envía lo que quiera. O
> usa `curl` y se salta el formulario entero. La validación de verdad es la del
> servidor; esta solo evita que un usuario honesto se equivoque.

### Bloque C — HTML seguro (mínimo 2)

- **Ningún `<script>` dentro del HTML.** El JavaScript llega en la clase 03, y
  llegará en su propio archivo.
- **La CSP está declarada** en todas las páginas.
- **El `<title>` no filtra datos.** Nada de «Panel de administración» ni el
  nombre del usuario en el título de la pestaña: sale en el historial, en las
  capturas y en la lista de pestañas.
- **Ningún enlace externo con `target="_blank"` sin `rel="noopener"`.** Sin eso,
  la página de destino puede manipular la tuya desde `window.opener`.

---

## Las tres vistas, y las dependencias de terceros

Vuestra web son **tres páginas con un diseño coherente**:

| Página | Qué es |
|--------|--------|
| `login.html` | La puerta de entrada. Ya la tenéis |
| `register.html` | El alta de usuario. Es la tarea 1 |
| `mi-panel.html` | El panel: tarjetas de resumen y tabla de datos |

> El panel tendrá **submenús** más adelante. Dejad hueco para la navegación
> cuando pidáis el diseño a la IA.

### Y la dependencia externa: traedla a casa

En clase enlazasteis Pico.css desde una CDN y funcionó. Ahora quitadle el
riesgo. Es fácil porque Pico es **un único archivo de 82 KB, sin fuentes ni
imágenes externas**:

```bash
mkdir -p frontend/vendor
curl -o frontend/vendor/pico.min.css \
  https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css
```

Y en vuestras páginas:

```html
<link rel="stylesheet" href="/vendor/pico.min.css">
```

**Comprobad las dos cosas** tras `docker compose up -d --build frontend`:

1. La web se sigue viendo igual de bien.
2. Con `<meta http-equiv="Content-Security-Policy" content="default-src 'self'">`
   activa, **ahora sí carga**. Con la CDN, esa misma CSP la habría bloqueado.

> 💡 Si por lo que sea tenéis que dejar una dependencia en una CDN, lo mínimo
> exigible es **SRI**: `integrity="sha384-..."` + `crossorigin="anonymous"`.
> Si el archivo cambia un solo byte, el navegador lo rechaza. Es **OWASP A08**.

---

## 🏆 El problema interesante (esto es lo que más nota vale)

En clase pusisteis este metadato en vuestras páginas:

```html
<meta http-equiv="X-Frame-Options" content="DENY">
```

Y comprobasteis en `http://localhost:8080/demo-iframe.html` que **no protege de
nada**: el login se sigue viendo dentro del iframe.

Ahora la pregunta:

> **Si escribes un test que compruebe «el meta está en el HTML», ese test estará
> en VERDE certificando una protección que no existe.**
>
> Eso es un **falso verde**, y es peor que no tener test: te da confianza sin
> darte seguridad.

**Tu tarea:** escribe un test que compruebe lo que **de verdad** importa.

Tienes el ejemplo resuelto en el archivo: `test_dinamico_el_meta_no_se_convierte_en_cabecera`.
Léelo, entiéndelo, y **escribe el equivalente para `X-Content-Type-Options`**,
que tiene exactamente el mismo problema.

En el docstring explica, con tus palabras, la diferencia entre:
- lo que ve un test **estático** (lo que está escrito), y
- lo que ve un test **dinámico** (lo que realmente ocurre).

---

## Cómo se ejecuta y se entrega

```bash
# Los tuyos, sin levantar nada
./.venv/bin/pytest tests/test_clase02_html_css.py -v

# Todo junto, clase 1 y clase 2 (necesita el laboratorio encendido)
make fase3-web
./.venv/bin/pytest tests/ -v

git add . && git commit -m "Clase 02: tests de HTML semántico y accesible"
git push
```

Y mira la pestaña **Actions** de tu GitHub: el workflow ejecuta primero los
estáticos y luego los dinámicos. Tus tests nuevos entran solos, sin tocar nada.

---

## Cómo se evalúa

| Criterio | Peso |
|----------|------|
| Los 6 tests mínimos, repartidos en los tres bloques | 30 % |
| Cada test con su docstring: OBJETIVO y POSIBLES RESULTADOS | 25 % |
| El `assert` lleva mensaje útil, no genérico | 20 % |
| El test de `X-Content-Type-Options` bien razonado | 25 % |

---

## Dos reglas que ya conocéis y siguen valiendo

**Un test que nunca has visto fallar no es un test.** Rompe cada uno a propósito
—quita el `lang="es"`, mete un `onclick=`— y comprueba que salta. Si no salta,
no estaba comprobando nada.

**El mensaje del `assert` se escribe para el día del desastre.** No para hoy,
que sabes lo que hace. Para dentro de tres semanas, cuando algo se rompa y solo
tengas esa línea.

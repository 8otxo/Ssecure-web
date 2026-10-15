# Tests por clase — secure-web-lab

Cada clase añade su archivo. Los tests **nunca se borran**: se acumulan, y la
suite entera se ejecuta en cada `push` (ver `.github/workflows/tests.yml`).

| Clase | Archivo | Estado |
|-------|---------|--------|
| 01 | `test_clase01_infra.py` — la web y la red (10 tests) | ✅ Hecho en clase |
| 02 | `test_clase02_html_css.py` — HTML semántico y metadatos (13 tests) | ✅ Hecho en clase |
| 03 | `test_clase03_js_security.py` | 📝 Pendiente |
| 04 | `test_clase04_nginx.py` | 📝 Pendiente |
| 05 | `test_clase05_cookies.py` | 📝 Pendiente |
| 06 | `test_clase06_jwt_rbac.py` | 📝 Pendiente |
| 07 | `test_clase07_https.py` | 📝 Pendiente |
| 08 | `test_clase08_headers.py` | 📝 Pendiente |

---

## Cómo se ejecutan

```bash
make test-fase3     # clase 01 (10) · necesita la web levantada: make fase3-web
make test-clase02   # clase 02 (13) · 12 son estáticos, van con el lab apagado
make test-todo      # las dos suites juntas
```

> Si ves `pytest: command not found`, ejecuta `make setup`: recrea el entorno
> virtual. Y ejecuta siempre desde la raíz del proyecto, no desde `tests/`.

---

## Estáticos y dinámicos

Es la distinción que vertebra la asignatura:

| | Qué mira | Necesita Docker | En la industria |
|---|---|---|---|
| **Estático** | lo que está **escrito** en los archivos | ❌ No | SAST |
| **Dinámico** | lo que **realmente ocurre** al ejecutar | ✅ Sí | DAST |

Por eso el nombre de cada test empieza por `test_estatico_` o `test_dinamico_`,
y por eso la tubería de GitHub Actions ejecuta **primero los estáticos**: son
los más baratos, y si fallan no merece la pena levantar nada.

El caso que mejor lo ilustra es `test_dinamico_el_meta_no_se_convierte_en_cabecera`
(clase 02): un test estático confirmaría que `<meta http-equiv="X-Frame-Options">`
está escrito en el HTML, y se pondría **verde certificando una protección que no
existe**. El dinámico comprueba la respuesta real del servidor y demuestra que
esa cabecera nunca llega. Eso es un **falso verde**.

---

## La fase 4 no tiene tests

Es deliberado. La fase 4 (mitm + sniffer) es una **demostración**: sirve para
ver la contraseña viajando en claro, no para verificar el proyecto. Se comprueba
a ojo:

```bash
make credenciales   # las dos capturas juntas
make demo-pasivo    # logs en vivo del sniffer (L3/L4)
make demo-activo    # logs en vivo del mitm (L7)
```

---

## Dos reglas que valen para todo el curso

**Si no hay un test que lo compruebe, no está hecho.**

**Un test que nunca has visto fallar no es un test.** Rómpelo a propósito —quita
el `lang="es"`, mete un `onclick=`— y comprueba que salta. Si no salta, no
estaba comprobando nada.

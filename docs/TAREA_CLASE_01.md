# TAREA — Escribe los tests de tu plan de red

**Entrega:** `tests/test_clase01_red.py` en tu repositorio de GitHub
**Se corrige en común al empezar la clase 02**
**Solo necesitas la fase 3:** `make fase3-web`

En la fase 1 decidisteis, en papel, **qué contenedor podía hablar con cuál y qué
puertos se publicaban**. Ahora esa decisión tiene que dejar de ser un papel y
pasar a ser código que se ejecuta solo. Es la casilla **CI** de la tubería
DevSecOps: el pipeline no «revisa» la arquitectura, la **comprueba** en cada cambio.

---

## Punto de partida: lo que YA tienes

Abre `tests/test_clase01_infra.py`. Trae 10 tests comentados línea a línea, y
son tu plantilla. Dos de ellos ya cubren parte del trabajo:

| Ya hecho, no lo repitas | Tipo |
|-------------------------|------|
| `test_estatico_la_bd_no_declara_puertos` | lee el YAML |
| `test_estatico_cada_servicio_esta_en_su_red` | lee el YAML |
| `test_dinamico_la_bd_no_esta_publicada` | pregunta a Docker |

**Tu trabajo no es copiarlos: es ampliarlos.** Abajo te digo exactamente qué falta.

Recuerda la diferencia, porque la tarea la usa constantemente:

- **ESTÁTICO** → lee `docker-compose.yml`. Funciona con el laboratorio apagado.
  Responde a *«¿qué hemos pedido?»*
- **DINÁMICO** → interroga al laboratorio en marcha. Responde a *«¿qué hay
  realmente?»*

---

## El problema interesante (léelo antes de empezar)

Hoy el laboratorio **incumple** parte de su propio diseño:

- El `backend` publica el puerto 8000: una ruta directa a la API que se salta
  el proxy.
- Y algo más que vas a descubrir tú en el bloque C.

¿Qué haces con un test que comprueba algo que **hoy no se cumple**?

| Opción | Qué pasa | Veredicto |
|--------|----------|-----------|
| No escribir el test | La deuda se olvida | ❌ Como no tenerla |
| Escribirlo «al revés» (*compruebo que el 8000 SÍ está publicado*) | Verde certificando un fallo, y el día que se arregle parecerá una regresión | ❌ Normaliza lo inseguro |
| **Escribir el test correcto y marcarlo como deuda conocida** | Dice lo que **debe** cumplirse, hoy falla, y el sistema lo sabe | ✅ |

La tercera se hace con `xfail`:

```python
import pytest

@pytest.mark.xfail(
    strict=True,
    reason="DEUDA: el backend publica el 8000 para ver Swagger en clase 1. Se cierra en la clase 04.",
)
def test_backend_no_publica_puertos():
    """El backend NO debe ser alcanzable desde el host: hay que pasar por el proxy."""
    ...
```

Qué consigues:

- **El test siempre dice lo correcto.** Nunca escribes «compruebo que es
  inseguro»: escribes el requisito, y aparte declaras que aún no se cumple.
- **Hoy la suite está verde.** Pytest lo marca `XFAIL`. No te acostumbras a
  convivir con rojos, que es como se acaban ignorando.
- **El día que se arregle, te avisa.** En la clase 04 quitaremos ese `ports:`;
  el test pasará y con `strict=True` pytest lo marca `FAILED [XPASS(strict)]`
  — *«esto ya funciona, quita la marca»*. La deuda no se cierra en silencio.

> **La pregunta obvia:** si la seguridad es desde el principio, ¿por qué el lab
> es inseguro? Porque en un proyecto real **tampoco** tienes todo desde el día
> uno. Lo que sí puedes tener es el **requisito escrito y vigilado**. La
> diferencia entre deuda técnica y chapuza es que la deuda está registrada,
> tiene dueño y tiene fecha. El `reason=` es ese registro.

---

## Qué tienes que entregar

`tests/test_clase01_red.py` con **mínimo 6 tests**, repartidos así:

### Bloque A — Segmentación (mínimo 1 test) · DINÁMICO

El estático ya está hecho en el archivo de ejemplo. **Te falta el dinámico:**
comprobar que las redes **reales** de cada contenedor coinciden con las
declaradas. Es el detector de *drift*: si alguien conectó un contenedor a otra
red a mano, el YAML seguirá diciendo que todo va bien.

```bash
docker inspect secure-web-lab-db-1 --format '{{json .NetworkSettings.Networks}}'
```

Devuelve un JSON cuyas claves son los nombres de red, con el prefijo del
proyecto (`secure-web-lab_web_net`).

| Contenedor | Redes esperadas |
|------------|-----------------|
| `db`, `backend` | solo `web_net` |
| `frontend` | `ruta_usuario` **y** `web_net` (es el único puente) |

### Bloque B — Exposición (mínimo 2 tests)

| Debe cumplirse | ¿Hoy? |
|----------------|-------|
| El `backend` **no** publica el 8000 | **No → `xfail`** |
| El `frontend` **sí** publica su puerto (es la puerta de entrada) | Sí |

Los puertos publicados salen de `docker compose ps --format json`, campo
`Publishers` (cada uno tiene `PublishedPort`; 0 o vacío = no publicado). Tienes
el código resuelto en `test_dinamico_la_bd_no_esta_publicada`: cópialo y
adáptalo.

Haz el del backend **estático y dinámico** si quieres nota extra: el YAML y la
realidad pueden discrepar.

### Bloque C — Alcance real (mínimo 3 tests) · DINÁMICO

Los bloques A y B leen **declaraciones**. Este comprueba la **realidad
conectando de verdad**, y no siempre coinciden. Se hace desde dentro de un
contenedor:

```bash
docker compose exec -T backend python3 -c "import socket; socket.create_connection(('db',5432),timeout=3)"
docker compose exec -T frontend nc -z -w3 db 5432
```

Comprueba al menos estos tres:

| Sonda | ¿Debería? | ¿Hoy? |
|-------|-----------|-------|
| `frontend` → `backend:8000` | **Sí**, es su trabajo (proxy `/api/`) | Sí ✅ |
| `backend` → `db:5432` | **Sí**, es el único que habla con la BD | Sí ✅ |
| `frontend` → `db:5432` | **NO**, NGINX no tiene nada que hacer ahí | ⚠️ **compruébalo** |

> 🏆 **El punto que más nota vale.** Ese tercero: NGINX solo hace de proxy hacia
> el backend, así que no debería poder ni ver la base de datos. **Compruébalo
> antes de asumir nada.** Si resulta que sí la alcanza, has encontrado una deuda
> que no estaba en el guion: regístrala con su `xfail` y su `reason` explicando
> qué habría que cambiar en el diseño.

> ⚠️ **Cuidado con el sondeo.** No todos los contenedores traen las mismas
> herramientas: `nginx:alpine` tiene `nc` y `wget` pero **no** `python3`;
> `python:3.12-slim` al revés. Si sondeas con algo que no existe, el comando
> falla y tu test dará por hecho «no alcanza»: **pasará por el motivo
> equivocado**. Un falso verde es peor que no tener test. Mira primero qué hay:
>
> ```bash
> docker compose exec frontend sh -c "command -v python3 nc wget"
> ```
>
> Y si no hay con qué comprobar, usa `pytest.skip()`. Nunca te inventes el
> resultado.

### Opcional, para subir nota

- La `db` no debería tener salida a Internet. ¿La tiene?
- El `backend` tampoco. ¿Y él?
- Regístralos como `xfail` con motivo y clase de cierre.

---

## Además, una tabla en tu informe

| Decisión de la fase 1 | Test que la vigila | Estado hoy | Se cierra en |
|-----------------------|--------------------|------------|--------------|
| La BD no se publica | `test_dinamico_la_bd_no_esta_publicada` | ✅ PASS | — |
| El backend no se publica | `test_backend_no_publica_puertos` | ⚠️ XFAIL | Clase 04 |
| … | … | … | … |

Esa tabla es tu **registro de deuda de seguridad**. En una empresa se llama
*risk acceptance* y lleva firma y fecha de caducidad.

---

## Cómo ejecutarlo

```bash
make fase3-web
./.venv/bin/pytest tests/test_clase01_red.py -v -rxX
```

`-rxX` hace que pytest **liste** al final los XFAIL y los XPASS en vez de
esconderlos. Salida sana: varios `PASSED` y unos pocos `XFAIL` con su motivo.
**Ni un solo `FAILED`.**

> Los tests estáticos funcionan incluso con el laboratorio apagado. Pruébalo:
> `make down` y luego `pytest tests/test_clase01_red.py -k estatico`

---

## Cómo se evalúa

| Criterio | Peso |
|----------|------|
| Los tests expresan el **requisito**, nunca la vulnerabilidad | 30 % |
| Cada `xfail` tiene `reason` concreto y la clase en que se cierra | 25 % |
| Cubre los tres bloques (segmentación, exposición, alcance real) | 25 % |
| Descubre alguna deuda que no estaba en el guion | 20 % |

---

## Pistas para no atascarte

- **Copia la estructura de `tests/test_clase01_infra.py`.** Ya tiene los
  ayudantes `_leer_compose()` y `_compose()` resueltos y comentados. Reutilízalos.
- Los nombres de los contenedores llevan prefijo del proyecto:
  `secure-web-lab-db-1`. Los nombres de red también: `secure-web-lab_web_net`.
- **Un test que no has visto fallar nunca no es un test.** Rómpelo a propósito
  una vez —cambia el nombre de la red esperada— y comprueba que salta. Si no
  salta, no estaba comprobando nada.

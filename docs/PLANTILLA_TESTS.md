# La anatomía de un archivo de tests

Sí, existe una plantilla, y es **la misma para todos los tests del curso**.
Cualquier archivo de tests tiene estas cinco partes, siempre en este orden.

```python
"""1 · DOCSTRING — qué comprueba este archivo y qué hace falta para ejecutarlo."""

# 2 · IMPORTS
import pytest

# 3 · CONSTANTES  (rutas, nombres, valores que se repiten)
RUTA_COMPOSE = "docker-compose.yml"

# 4 · HELPERS  (lo que se repite en varios tests; NO empiezan por test_)
def leer_algo():
    ...

# 5 · TESTS  (uno por requisito; SÍ empiezan por test_)
def test_el_requisito_que_comprueba():
    """Frase que explica el requisito en lenguaje humano."""
    resultado = leer_algo()          # Preparar + Actuar
    assert resultado == lo_esperado  # Comprobar
```

---

## Las tres reglas que hay que memorizar

**1. Pytest encuentra los tests por el nombre.**
Archivo `test_*.py`, funciones `test_*()`. Si no empieza por `test_`, pytest ni lo
mira — por eso los *helpers* no llevan ese prefijo: no queremos que se ejecuten
solos, queremos reutilizarlos.

**2. Un test = un requisito.**
Si un test comprueba tres cosas y falla, no sabes cuál de las tres. El nombre debe
ser una frase que puedas leer en voz alta: `test_db_no_publica_puertos` te dice
qué se rompió sin abrir el código.

**3. El patrón AAA: Preparar → Actuar → Comprobar.**
En inglés *Arrange, Act, Assert*. Es el esqueleto de **todo** test del mundo:

```python
def test_db_no_publica_puertos():
    """La base de datos no debe ser alcanzable desde el host."""
    compose = leer_compose()                    # Preparar: consigo los datos
    puertos = compose["services"]["db"].get("ports", [])   # Actuar: hago la operación
    assert puertos == [], f"La BD publica {puertos}"       # Comprobar: ¿es lo esperado?
```

---

## `assert`: la única instrucción que necesitas

`assert <condición>, "mensaje si falla"`

- Si la condición es cierta → el test pasa, en silencio.
- Si es falsa → el test falla y te enseña **tu** mensaje.

**Pon siempre el mensaje.** Compara estas dos salidas cuando algo se rompe:

```
E       assert [] == ['8000:8000']                    ← ¿y esto qué significa?
E       AssertionError: La BD publica ['5432:5432']   ← esto se entiende solo
```

---

## Dos herramientas más que usarás hoy

### `@pytest.mark.xfail` — para lo que aún no se cumple

```python
@pytest.mark.xfail(strict=True, reason="DEUDA: se cierra en la clase 04")
def test_backend_no_publica_puertos():
    ...
```

El test **sigue diciendo lo correcto**; solo declaras que hoy falla a propósito.
La suite queda verde y, cuando se arregle, pytest te avisa para que quites la marca.

### `pytest.skip()` — cuando no puedes comprobarlo

```python
if not hay_con_que_comprobarlo:
    pytest.skip("El contenedor no tiene python3 ni nc")
```

**Nunca devuelvas «no» cuando en realidad es «no lo sé».** Un test que pasa porque
la comprobación no se pudo hacer es un falso verde, y es peor que no tener test.

---

## Plantilla lista para copiar

```python
"""Tests de arquitectura — Clase 01.

Comprueban que la red del laboratorio es la que diseñamos en la fase 1.

Ejecutar:
    make fase4-ataque
    ./.venv/bin/pytest tests/test_clase01_red.py -v -rxX
"""
import json
import os
import subprocess

import pytest
import yaml

# --- Constantes -----------------------------------------------------------
RAIZ = os.path.dirname(os.path.dirname(__file__))   # carpeta del laboratorio
COMPOSE = os.path.join(RAIZ, "docker-compose.yml")
ENV = {**os.environ, "COMPOSE_PROFILES": "ataque"}  # para ver a los atacantes


# --- Helpers --------------------------------------------------------------
def leer_compose():
    """Lee el docker-compose.yml y lo devuelve como diccionario de Python."""
    with open(COMPOSE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def docker(*args):
    """Ejecuta `docker ...` y devuelve el resultado."""
    return subprocess.run(
        ["docker", *args], capture_output=True, text=True, timeout=30,
        cwd=RAIZ, env=ENV,
    )


# --- Tests ----------------------------------------------------------------
def test_ejemplo():
    """Una frase que explique el requisito."""
    datos = leer_compose()                     # Preparar
    valor = datos["services"]["db"].get("ports", [])   # Actuar
    assert valor == [], f"Mensaje claro: {valor}"      # Comprobar
```

---

## Cómo ejecutarlos

```bash
./.venv/bin/pytest tests/test_clase01_red.py -v -rxX
```

| Opción | Para qué |
|--------|----------|
| `-v` | Lista los tests uno a uno con su resultado |
| `-rxX` | Muestra al final el motivo de los XFAIL y los XPASS |
| `-k red` | Ejecuta solo los tests cuyo nombre contenga «red» |
| `-x` | Se para en el primer fallo |

**Lectura de resultados:**

| Símbolo | Significa |
|---------|-----------|
| `PASSED` | El requisito se cumple ✅ |
| `FAILED` | El requisito NO se cumple y no lo sabías ❌ |
| `XFAIL` | No se cumple, pero está registrado como deuda ⚠️ |
| `XPASS` | ¡Ya se cumple! Quita la marca de deuda 🎉 |
| `SKIPPED` | No se pudo comprobar (¿falta levantar el lab?) |

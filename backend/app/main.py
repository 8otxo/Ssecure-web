"""Backend intencionalmente inseguro — clase 01. Mejoras progresivas en clases siguientes."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://securelab:securelab_dev_only@db:5432/securelab")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(64) UNIQUE NOT NULL,
                password_plain VARCHAR(128) NOT NULL
            )
        """))
        conn.commit()
        result = conn.execute(text("SELECT COUNT(*) FROM users WHERE username = :u"), {"u": ADMIN_USERNAME})
        if result.scalar() == 0:
            conn.execute(
                text("INSERT INTO users (username, password_plain) VALUES (:u, :p)"),
                {"u": ADMIN_USERNAME, "p": ADMIN_PASSWORD},
            )
            conn.commit()
    yield


app = FastAPI(title="Secure Web Lab API", lifespan=lifespan)

# CORS abierto — A02 misconfiguration (se endurece en clases posteriores)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# Dos rutas para la misma función. /api/login es la que usa el formulario y la
# que usan los tests; /login se mantiene porque nginx tiene una regla para ella.
# (Antes solo existía /login y funcionaba porque nginx recortaba el prefijo
#  /api/. Al dejar de recortarlo para poder servir /api/documentos, hubo que
#  nombrar la ruta tal y como se pide de verdad. Un cambio de una línea en el
#  proxy movió el suelo de toda la API: por eso el enrutado se documenta.)
@app.post("/api/login")
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    """Login inseguro: compara contraseña en texto plano, cookie sin flags seguros."""
    with SessionLocal() as db:
        row = db.execute(
            text("SELECT id, username, password_plain FROM users WHERE username = :u"),
            {"u": username},
        ).fetchone()
        if not row or row.password_plain != password:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    # POST-Redirect-GET. En la clase 01 el formulario es HTML puro: sin
    # JavaScript (llega en la clase 03) el navegador se queda en la respuesta
    # del POST. Es el servidor quien tiene que decirle a dónde ir, y el 303
    # convierte ese POST en un GET a /panel.html.
    response = RedirectResponse(url="/panel.html", status_code=303)

    # Cookie de sesión insegura — se corrige en clase 05.
    # Sigue siendo insegura a propósito: valor predecible (`user-<username>`),
    # sin HttpOnly (legible por JS → robable vía XSS) y sin Secure (viaja por HTTP,
    # el proxy `mitm` la lee en claro). NO usamos samesite="none": los navegadores
    # modernos descartan una cookie SameSite=None que no lleve Secure, y la cookie
    # ni se almacenaría (rompería el login). Lax es el valor por defecto del navegador.
    response.set_cookie(key="session_id", value=f"user-{username}", httponly=False, secure=False, samesite="lax")
    return response


@app.get("/api/me")
def me(session_id: str | None = None):
    if not session_id:
        raise HTTPException(status_code=401, detail="No autenticado")
    if session_id.startswith("user-"):
        return {"username": session_id.replace("user-", "", 1)}
    raise HTTPException(status_code=401, detail="Sesión inválida")


# ---------------------------------------------------------------- CLASE 03 ---
# Endpoint de solo lectura para el panel. Es el primero que el frontend va a
# consumir con fetch(), y el que introduce la idea de "API que devuelve JSON".
#
# OJO AL TERCER DOCUMENTO. Su nombre es una carga de XSS. Está aquí a propósito:
# un atacante no ataca escribiendo en tu JavaScript, ataca metiendo datos en tu
# base de datos y esperando a que alguien los pinte. Si el frontend usa
# innerHTML, ese nombre se ejecuta. Si usa textContent, se lee como texto.
DOCUMENTOS_DEMO = [
    {"id": 1, "nombre": "contrato-marco-2026.pdf", "tamano_kb": 248,
     "subido": "2026-09-21", "estado": "analizado"},
    {"id": 2, "nombre": "memoria-anual.docx", "tamano_kb": 1024,
     "subido": "2026-09-22", "estado": "pendiente"},
    {"id": 3, "nombre": ("<img src=x onerror=\"document.querySelector('.org')"
                         ".textContent='XSS EJECUTADO';document.querySelector"
                         "('.org').style.color='#c00'\">"),
     "tamano_kb": 12, "subido": "2026-09-23", "estado": "analizado"},
    {"id": 4, "nombre": "acta-reunion-09.txt", "tamano_kb": 38,
     "subido": "2026-09-24", "estado": "analizado"},
]


@app.get("/api/documentos")
def listar_documentos():
    """Devuelve los documentos de la organización.

    Inseguro a propósito, como todo el laboratorio hasta su clase:
      · no pide sesión: cualquiera lo consulta        -> A01 (clase 06)
      · no filtra por organización: no hay aislamiento -> API1 (clase 06)
      · devuelve el dato tal cual lo tiene guardado    -> el XSS es de clase 03
    """
    return {"documentos": DOCUMENTOS_DEMO}


# ---------------------------------------------------------------- CLASE 04 ---
# El resto de pestañas del panel. Todas de solo lectura y con datos de ejemplo:
# el backend de verdad lo construyen en Programación Segura.
#
# Igual que /api/documentos, ninguna pide sesión todavía. Es deuda declarada:
#   · sin autenticación           -> A01, se cierra en la clase 06
#   · sin aislamiento por empresa -> API1, se cierra en la clase 06
ANALISIS_DEMO = [
    {"id": 1, "documento": "contrato-marco-2026.pdf", "tipo": "resumen",
     "estado": "completado", "duracion_s": 12},
    {"id": 2, "documento": "memoria-anual.docx", "tipo": "clasificación",
     "estado": "en curso", "duracion_s": 0},
    {"id": 3, "documento": "acta-reunion-09.txt", "tipo": "resumen",
     "estado": "completado", "duracion_s": 4},
    {"id": 4, "documento": "contrato-marco-2026.pdf", "tipo": "entidades",
     "estado": "error", "duracion_s": 31},
]

# OJO AL ROL. Todos son "admin", y eso está MAL a propósito.
# Un panel donde cualquiera administra a cualquiera es A01 Broken Access
# Control de manual. Se arregla en la clase 06, cuando haya roles de verdad.
USUARIOS_DEMO = [
    {"id": 1, "nombre": "Ana Gorbea",    "correo": "ana@euneiz.com",
     "rol": "admin", "alta": "2026-01-12", "estado": "activo"},
    {"id": 2, "nombre": "Luis Mendieta", "correo": "luis@euneiz.com",
     "rol": "admin", "alta": "2026-02-03", "estado": "activo"},
    {"id": 3, "nombre": "Nerea Aguirre", "correo": "nerea@euneiz.com",
     "rol": "admin", "alta": "2026-03-21", "estado": "invitado"},
    {"id": 4, "nombre": "Jon Etxebarria", "correo": "jon@euneiz.com",
     "rol": "admin", "alta": "2026-05-08", "estado": "suspendido"},
]

SUSCRIPCION_DEMO = {
    "plan": "pro",
    "documentos_usados": 4,
    "documentos_incluidos": 50,
    "analisis_usados": 4,
    "analisis_incluidos": 100,
    "renovacion": "2026-11-01",
}


@app.get("/api/analisis")
def listar_analisis():
    """Análisis lanzados sobre los documentos."""
    return {"analisis": ANALISIS_DEMO}


@app.get("/api/usuarios")
def listar_usuarios():
    """Usuarios de la organización. Todos admin: deuda declarada (A01)."""
    return {"usuarios": USUARIOS_DEMO}


@app.get("/api/suscripcion")
def consultar_suscripcion():
    """Plan contratado y consumo del mes."""
    return {"suscripcion": SUSCRIPCION_DEMO}


# ---------------------------------------------------------------- CLASE 04 ---
# Misma comprobación de salud que /health, pero bajo /api/ para que se pueda
# preguntar POR EL PROXY. Hace falta a partir de la clase 04: cuando el puerto
# 8000 deje de estar publicado, la única vía será la puerta principal.
@app.get("/api/health")
def health_por_el_proxy():
    return {"status": "ok"}


@app.get("/api/eco")
def eco(request: Request):
    """Devuelve lo que el BACKEND ve de la petición. Solo para el laboratorio.

    Sirve para responder a una pregunta que no se puede contestar de otra
    forma: cuando el navegador habla con nginx y nginx habla con la API,
    ¿qué le llega exactamente a la API?

    Aquí se ve el efecto de proxy_set_header: X-Real-IP y X-Forwarded-For los
    añade nginx, no el navegador.

    ⚠️ Un endpoint que devuelve las cabeceras recibidas NO se publica en
    producción: le enseña a cualquiera cómo está montada tu infraestructura.
    Está aquí porque esto es un laboratorio y hay que poder mirar dentro.
    """
    interesantes = ("host", "user-agent", "x-real-ip", "x-forwarded-for",
                    "x-forwarded-proto", "referer", "cookie")
    return {
        "metodo": request.method,
        "ruta": request.url.path,
        "cliente": request.client.host if request.client else None,
        "cabeceras": {k: v for k, v in request.headers.items() if k.lower() in interesantes},
    }


@app.post("/api/register")
def registrar():
    """El alta de usuario todavía no existe. Y se dice con un 501, no con un 404.

    La diferencia importa:
      · 404 Not Found      -> "esto no existe". El cliente no sabe si se ha
                              equivocado de ruta o si es que falta algo.
      · 501 Not Implemented-> "existe, pero aún no lo he construido". Es una
                              respuesta honesta y le dice al cliente que no
                              siga intentándolo.

    Crear usuarios de verdad necesita contraseñas bien guardadas, y eso es
    materia de Programación Segura y de la clase 06. Hasta entonces el
    formulario sirve para practicar la validación del cliente, que es lo que
    toca en la clase 03.
    """
    raise HTTPException(
        status_code=501,
        detail="El alta de usuario llega en la clase 06. Hoy el formulario "
               "sirve para practicar la validación en el cliente.",
    )

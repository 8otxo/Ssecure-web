# EMPIEZA AQUÍ

**Desarrollo Web Seguro · Clase 01 · Grado en Ciberseguridad (EUNEIZ)**

Acabas de descomprimir el laboratorio del curso. Esta es tu web, y durante el
semestre la iremos haciendo segura. Hoy no lo es: eso es a propósito.

---

## Los 4 documentos que necesitas

| Quiero… | Abre |
|---------|------|
| 🚀 **Instalar y arrancar** (Windows, VM, WSL, Linux) | `docs/COMO_EJECUTARLO.md` |
| 📖 **Seguir el laboratorio paso a paso** | `README.md` → sección **«Guion de clase»** |
| 🐙 **Subirlo a mi GitHub** | `docs/GUIA_GIT_GITHUB.md` |
| 📝 **Hacer la tarea para la próxima clase** | `docs/TAREA_CLASE_01.md` |

Y si te pierdes en cualquier momento:

```bash
make ayuda          # Windows PowerShell:  .\lab.ps1 ayuda
```

---

## Arranque rápido (3 comandos)

```bash
cd secure-web-lab

make setup          # comprueba Docker, prepara el entorno y las dependencias
make fase1-red      # te dice cómo está tu máquina y qué vamos a construir
make fase3-web      # levanta la web  →  http://localhost:8080
```

En Windows sin WSL, cambia `make X` por `.\lab.ps1 X`. Los nombres son idénticos.

**Credenciales de la web:** `admin` / `admin123`

> ⚠️ ¿Estás en una **máquina virtual**? `localhost` dentro de la VM **no** es el
> `localhost` del navegador de Windows. `make setup` lo detecta y te lo avisa;
> la solución está en `docs/COMO_EJECUTARLO.md`.

---

## ⚠️ ANTES de subir esto a GitHub: lo que NO debe salir de tu equipo

`git add .` sube **todo** lo que hay en la carpeta. Y aquí hay cosas que no deben
llegar nunca a un repositorio:

| Archivo | Por qué |
|---------|---------|
| **`.env`** | Contiene `ADMIN_PASSWORD`, `SECRET_KEY` y la contraseña de la base de datos |
| `.venv/` | 25 MB de dependencias; se regeneran solas con `make setup` |
| `__pycache__/`, `.pytest_cache/` | Archivos temporales |
| `*.log`, `*.db` | Capturas y datos locales tuyos |

### Cómo se ignoran

Con un archivo llamado **`.gitignore`**, que enumera lo que Git debe saltarse.
**Este laboratorio ya trae uno preparado** — ábrelo y léelo, está comentado:

```bash
cat .gitignore
```

Y adquiere este hábito desde hoy: **antes de cada `git commit`, mira qué vas a
subir**.

```bash
git add .
git status          # ← ¿aparece .env o .venv? Entonces PARA
```

> 🔴 **Un secreto subido a GitHub se considera comprometido para siempre**, aunque
> borres el commit después: queda en el historial, y hay bots rastreando GitHub
> que lo encuentran en minutos. Por eso se sube `.env.example` (la plantilla, sin
> valores reales) y **nunca** `.env`.
>
> Este `.env` solo tiene credenciales de laboratorio, así que hoy no pasa nada.
> El hábito es lo que importa: el día que sea la clave real de un cliente, ya lo
> harás bien sin pensarlo.

**¿No tienes `.env`?** Es normal: no viene en el `.zip`, precisamente porque los
secretos no se distribuyen. `make setup` lo crea por ti a partir de
`.env.example`.

---

## Qué hay en cada carpeta

```
secure-web-lab/
├── EMPIEZA_AQUI.md      ← este archivo
├── README.md            ← guion del laboratorio + chuleta de comandos
├── docs/                ← las guías (instalación, GitHub, tarea, esquema de red)
├── lab.sh / lab.ps1     ← el lanzador (Linux-macOS-WSL / Windows)
├── Makefile             ← atajo: `make X` llama a `lab.sh X`
├── docker-compose.yml   ← el plan de la red: qué contenedores y cómo se conectan
├── backend/             ← la API (FastAPI + Python)
├── frontend/            ← la web (HTML/CSS servido por NGINX)
├── nginx/               ← configuración del proxy inverso
├── tests/               ← los tests automáticos (aquí entregarás la tarea)
├── mitm/  sniffer/      ← los dos atacantes, solo para la demo de la fase 4
└── .gitignore           ← lo que NO se sube a GitHub
```

---

## Aviso legal

Los contenedores `mitm` y `sniffer`, y las vulnerabilidades deliberadas de esta
aplicación, son **exclusivamente para uso educativo** dentro de la red Docker
aislada de tu equipo. No los uses en producción ni contra redes ajenas al
laboratorio.

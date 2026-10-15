# De la carpeta descargada a tu repositorio en GitHub

**Punto de partida:** has descargado `secure-web-lab.zip` del aula virtual y lo has
descomprimido. **Meta:** tenerlo en tu cuenta de GitHub y saber subir los cambios
de cada semana.

Todo el curso se entrega ahí, así que hazlo hoy aunque no hayas tocado código.

---

## Paso 0 — ¿Tienes Git?

```bash
git --version
```

Si responde algo como `git version 2.43.0`, sigue al paso 1. Si no:

| Sistema | Cómo instalarlo |
|---------|-----------------|
| **Windows** | https://git-scm.com/download/win · acepta las opciones por defecto |
| **macOS** | `xcode-select --install`, o `brew install git` |
| **Linux (Ubuntu/Debian)** | `sudo apt update && sudo apt install git` |

> En Windows el instalador trae **Git Bash**, una terminal tipo Linux. Úsala para
> todos los comandos de esta guía: te ahorra diferencias tontas.

---

## Paso 1 — Di quién eres (solo una vez por ordenador)

Cada commit lleva firmado tu nombre y correo. Si no los configuras, Git se niega
a hacer el primer commit.

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
```

> **Usa el mismo correo que asociarás a GitHub.** Si no coinciden, tus commits
> aparecerán como de un desconocido y no contarán en tu perfil.

Comprueba cómo ha quedado:

```bash
git config --global --list
```

---

## Paso 2 — Crea la cuenta y el repositorio

1. Cuenta en https://github.com (si ya tienes, sáltalo).
2. Arriba a la derecha: **+ → New repository**.
3. Rellena:
   - **Repository name:** `secure-web-lab`
   - **Private** ← recomendado: el laboratorio es vulnerable a propósito
   - **NO** marques «Add a README», «Add .gitignore» ni «Choose a license»

> **Por qué vacío:** si GitHub crea archivos, el repositorio remoto y el tuyo
> tendrán historias distintas y el primer `push` fallará con
> `rejected — fetch first`. Es el error nº 1 del primer día.

GitHub te enseñará una URL tipo `https://github.com/TU-USUARIO/secure-web-lab.git`.
Guárdala.

---

## Paso 3 — Antes de subir nada: mira qué vas a subir

**Este paso es el importante de la asignatura.** Un `git add .` sube *todo* lo que
hay en la carpeta, y en esa carpeta hay cosas que no deben salir de tu equipo:

| Archivo | Por qué NO debe subirse |
|---------|--------------------------|
| `.env` | Contiene `ADMIN_PASSWORD`, `SECRET_KEY` y la contraseña de la base de datos |
| `.venv/` | 25 MB de dependencias que se regeneran solas con `make setup` |
| `__pycache__/`, `.pytest_cache/` | Basura temporal |
| `*.log`, `*.db` | Capturas y datos locales |

Eso se declara en un archivo llamado **`.gitignore`**, y **este laboratorio ya
trae uno preparado**. Compruébalo:

```bash
cd ruta/de/secure-web-lab      # ajusta la ruta a donde lo descomprimiste
cat .gitignore
```

> **Un secreto subido a GitHub se considera comprometido para siempre**, aunque
> borres el commit después: queda en el historial, y hay bots que rastrean
> GitHub buscando credenciales en cuestión de minutos. Por eso se versiona
> `.env.example` (la plantilla, sin valores reales) y **nunca** `.env`.

Si en otro proyecto no tuvieras `.gitignore`, se crea antes del primer `add`.

---

## Paso 4 — Crea el repositorio y sube

Desde la carpeta del laboratorio:

```bash
cd ruta/de/secure-web-lab

git init                      # crea el repositorio local (carpeta .git oculta)
git add .                     # prepara todos los archivos... menos los de .gitignore
git status                    # ← PÁRATE AQUÍ Y MIRA
```

`git status` lista lo que se va a subir. **Confirma que NO aparecen `.env` ni
`.venv/`.** Si aparecen, revisa el `.gitignore` antes de seguir.

```bash
git commit -m "Clase 01: laboratorio inicial"
git branch -M main            # nombra la rama principal 'main'
git remote add origin https://github.com/TU-USUARIO/secure-web-lab.git
git push -u origin main       # sube y deja recordado el destino
```

---

## Paso 5 — La contraseña que no funciona

Al hacer `push`, GitHub te pedirá usuario y contraseña. **Tu contraseña de GitHub
no vale**: la retiraron en 2021. Verás algo así:

```
Support for password authentication was removed. Please use a personal access token.
```

Necesitas un **token**, que es una contraseña de un solo uso para herramientas:

1. GitHub → foto de perfil → **Settings**
2. Abajo del todo: **Developer settings**
3. **Personal access tokens → Tokens (classic) → Generate new token (classic)**
4. *Note:* `laboratorio DWS` · *Expiration:* 90 días
5. Marca la casilla **`repo`** (te da acceso a tus repositorios)
6. **Generate token** y **cópialo ahora**: no volverás a verlo

Cuando `git push` pida:
- **Username:** tu usuario de GitHub
- **Password:** *pega el token*

Para no repetirlo cada semana:

```bash
git config --global credential.helper store    # Linux (lo guarda en texto plano)
git config --global credential.helper manager  # Windows (Administrador de credenciales)
git config --global credential.helper osxkeychain   # macOS (Llavero)
```

---

## El día a día: cada vez que cambies algo

Estos tres comandos son el 95 % de tu uso de Git durante el curso:

```bash
git add .
git commit -m "Descripción de los cambios"
git push
```

Un mensaje de commit útil dice **qué** cambiaste y **por qué**:

- ❌ `cambios`, `update`, `asdf`
- ✅ `Clase 01: tests de segmentación de red con xfail para el puerto 8000`

Comandos que te sacarán de dudas:

| Comando | Para qué |
|---------|----------|
| `git status` | ¿Qué he tocado? ¿Qué se va a subir? |
| `git diff` | ¿Qué he cambiado exactamente? |
| `git log --oneline` | Historial de commits |

---

## Si algo falla

| Error | Qué significa y cómo se arregla |
|-------|--------------------------------|
| `Support for password authentication was removed` | Usa un token, no tu contraseña (paso 5) |
| `rejected ... fetch first` | Creaste el repo en GitHub con README. `git pull origin main --allow-unrelated-histories` y vuelve a hacer push |
| `Please tell me who you are` | Te falta el paso 1 |
| `remote origin already exists` | Ya lo añadiste. Corrígelo con `git remote set-url origin <URL>` |
| `src refspec main does not match any` | No has hecho ningún commit todavía |
| Subiste `.env` sin querer | Avísalo y **cambia las contraseñas**. Borrar el commit no basta |

---

## Comprobación final

En `https://github.com/TU-USUARIO/secure-web-lab` deberías ver:

- ✅ `docker-compose.yml`, `backend/`, `frontend/`, `tests/`, `README.md`
- ✅ `.env.example`
- ❌ **ni rastro de `.env` ni de `.venv/`**

Si esa última línea se cumple, has aprobado tu primer control de seguridad del
curso. Ese es el trabajo.

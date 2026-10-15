# Cómo ejecutar el laboratorio

Hay tres formas válidas. Elige la que te permitan los permisos de tu equipo.
**Ante la duda, ejecuta esto y te lo dice:**

```bash
./lab.sh entorno        # Windows PowerShell:  .\lab.ps1 entorno
```

## Lo que necesita el laboratorio (medido, no estimado)

| Recurso | Consumo real |
|---------|--------------|
| RAM de los 5 contenedores | **~150 MB** en total |
| Imágenes en disco | **~1 GB** (se descargan una vez) |
| CPU | despreciable en reposo |

Es un laboratorio ligero. Si usas una VM, con **4 GB de RAM, 2 vCPU y 20 GB de
disco** vas sobrado; el mínimo real son 2 GB de RAM.

---

## Opción A — Máquina virtual Linux *(la más probable)*

Si la universidad no te deja instalar Docker en tu portátil, esta es tu vía: en
la VM sí eres administrador.

1. Crea una VM con **Ubuntu 24.04** (4 GB RAM, 2 vCPU, 20 GB disco).
2. Dentro de la VM:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose-v2 git python3-venv
   sudo usermod -aG docker $USER
   ```
   **Cierra la sesión y vuelve a entrar** (si no, seguirás sin permiso sobre Docker).
3. Clona el repositorio dentro de la VM y lanza `./lab.sh setup`.

### El punto que da problemas: abrir la web desde Windows

Dentro de la VM, `http://localhost:8080` funciona siempre. Desde el navegador de
Windows depende de cómo esté configurada la red de la VM:

**Red en PUENTE (*bridged*) — recomendado**
La VM es una máquina más de la red del aula, con su propia IP.

```bash
hostname -I        # dentro de la VM: te da la IP, p.ej. 192.168.1.50
```
En Windows abres `http://192.168.1.50:8080`. Nada más que configurar.

**Red en NAT (la opción por defecto de VirtualBox)**
La VM no es visible desde fuera; hay que **reenviar puertos**:
*Configuración → Red → Avanzado → Reenvío de puertos*, y añade tres reglas:

| Nombre | Protocolo | Puerto anfitrión | Puerto invitado |
|--------|-----------|------------------|-----------------|
| web    | TCP       | 8080             | 8080            |
| limpio | TCP       | 8081             | 8081            |
| api    | TCP       | 8000             | 8000            |

Después, en Windows abres `http://localhost:8080` y llega a la VM.

> Con red en puente, la lección de seguridad de la clase 1 se ve de verdad: tu
> VM es una máquina más en la red del aula, así que un compañero puede abrir tu
> laboratorio escribiendo tu IP. Pruébalo entre dos VM.

---

## Opción B — Windows con Docker Desktop

Si tienes permisos de administrador en tu equipo.

1. Instala **Docker Desktop** con el backend **WSL2** (el instalador lo activa).
2. Abre PowerShell en la carpeta del laboratorio:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass   # solo si te bloquea
   .\lab.ps1 setup
   .\lab.ps1 fase1-red
   ```
3. `http://localhost:8080` funciona directamente en tu navegador.

Dos cosas que cambian respecto a Linux:

- Usa **`curl.exe`**, no `curl`: en PowerShell `curl` es `Invoke-WebRequest` y no
  entiende `-s`, `-X` ni `-d`.
- Si Docker Desktop no arranca: `wsl --status` y arráncalo antes de nada.

---

## Opción C — WSL2 (Linux dentro de Windows)

Lo mejor de las dos: terminal Linux y navegador de Windows sin configurar nada.

```powershell
wsl --install -d Ubuntu      # en PowerShell como administrador, una sola vez
```

Dentro de Ubuntu instalas Docker como en la Opción A y usas `./lab.sh`.
`http://localhost:8080` funciona **también en el navegador de Windows**: WSL2
reenvía el puerto solo.

> Si tienes Docker Desktop instalado, activa su integración con WSL en
> *Settings → Resources → WSL Integration* y te ahorras instalar Docker dentro.

---

## Problemas frecuentes

| Síntoma | Causa y solución |
|---------|------------------|
| `permission denied ... docker.sock` | Falta el grupo: `sudo usermod -aG docker $USER` y **reiniciar sesión** |
| `docker: command not found` | Docker no instalado, o no tienes permisos → usa la Opción A |
| `localhost:8080` no abre desde Windows, pero sí dentro de la VM | Red en NAT sin reenvío de puertos (ver tabla arriba) |
| `port is already allocated` | Otro proceso tiene el puerto: `./lab.sh fase1-red` te dice quién |
| La VM va muy lenta | Súbele RAM a 4 GB y activa la virtualización (VT-x/AMD-V) en la BIOS |
| `exec /sniff.sh: no such file or directory` | Los `.sh` llegaron con finales de línea CRLF (descarga por ZIP en Windows). Clona con Git, que respeta el `.gitattributes` |
| `pytest: command not found` | `./lab.sh setup` — recrea el entorno virtual |

## Qué hacer si no puedes con ninguna

Dilo en clase antes de empezar. Se puede trabajar en pareja con el equipo de un
compañero: el laboratorio aguanta de sobra dos personas trabajando, y las
prácticas están pensadas para hacerse en parejas.

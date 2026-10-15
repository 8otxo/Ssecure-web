/* ══════════════════════════════════════════════════════════════════════════
   VALIDACIÓN DEL FORMULARIO DE REGISTRO · clase 03
   ══════════════════════════════════════════════════════════════════════════
   Mismo aviso que en login.js: esto es EXPERIENCIA DE USO, no seguridad.
   Quien quiera saltárselo lo hace en diez segundos. La validación que
   protege es la del servidor.

   La diferencia con el login: aquí la contraseña se ELIGE. Por eso aquí SÍ
   se exige que sea fuerte, y en el login no.
   ══════════════════════════════════════════════════════════════════════════ */

const formulario = document.querySelector("form");
const nombre     = document.querySelector("#nombre");
const correo     = document.querySelector("#correo");
const nacimiento = document.querySelector("#nacimiento");
const clave      = document.querySelector("#password");
const clave2     = document.querySelector("#password2");


// ── Reglas ───────────────────────────────────────────────────────────────

// Devuelve la LISTA de lo que falta. Vacía = contraseña correcta.
function loQueFaltaEnLaClave(valor) {
  const falta = [];
  if (valor.length < 8)            falta.push("8 caracteres");
  if (!/[a-z]/.test(valor))        falta.push("una minúscula");
  if (!/[A-Z]/.test(valor))        falta.push("una mayúscula");
  if (!/[0-9]/.test(valor))        falta.push("un número");
  if (!/[^A-Za-z0-9]/.test(valor)) falta.push("un símbolo");
  return falta;
}

// Comprobación sencilla a propósito: algo, arroba, algo, punto, algo.
// La "expresión regular perfecta para correos" no existe; la única
// comprobación de verdad es enviar un correo y que lo reciban.
function pareceUnCorreo(valor) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor);
}

// Calcula la edad a partir de la fecha. Guardamos la FECHA, no la edad:
// una edad guardada se queda vieja ella sola al año siguiente.
function edadEnAnios(fechaTexto) {
  const nac = new Date(fechaTexto);
  if (isNaN(nac)) return null;
  const hoy = new Date();
  let edad = hoy.getFullYear() - nac.getFullYear();
  const mes = hoy.getMonth() - nac.getMonth();
  if (mes < 0 || (mes === 0 && hoy.getDate() < nac.getDate())) edad--;
  return edad;
}


// ── Mensajes de error ────────────────────────────────────────────────────

function marcarError(campo, mensaje) {
  quitarError(campo);

  const aviso = document.createElement("p");
  aviso.className = "error";
  aviso.id = campo.id + "-error";
  aviso.textContent = mensaje;          // TEXTO. Nunca innerHTML.

  campo.setAttribute("aria-invalid", "true");
  campo.setAttribute("aria-describedby", aviso.id);
  campo.after(aviso);
}

function quitarError(campo) {
  campo.removeAttribute("aria-invalid");
  campo.removeAttribute("aria-describedby");
  const viejo = document.getElementById(campo.id + "-error");
  if (viejo) viejo.remove();
}


// ── Al enviar ────────────────────────────────────────────────────────────

formulario.addEventListener("submit", (evento) => {
  let hayErrores = false;
  const campos = [nombre, correo, nacimiento, clave, clave2];
  campos.forEach(quitarError);

  if (nombre.value.trim() === "") {
    marcarError(nombre, "Escribe tu nombre.");
    hayErrores = true;
  }

  if (correo.value.trim() === "") {
    marcarError(correo, "Escribe tu correo.");
    hayErrores = true;
  } else if (!pareceUnCorreo(correo.value.trim())) {
    marcarError(correo, "Ese correo no tiene un formato válido.");
    hayErrores = true;
  }

  const edad = edadEnAnios(nacimiento.value);
  if (nacimiento.value === "") {
    marcarError(nacimiento, "Indica tu fecha de nacimiento.");
    hayErrores = true;
  } else if (edad === null || edad < 18) {
    marcarError(nacimiento, "Tienes que ser mayor de 18 años.");
    hayErrores = true;
  }

  const falta = loQueFaltaEnLaClave(clave.value);
  if (clave.value === "") {
    marcarError(clave, "Escribe una contraseña.");
    hayErrores = true;
  } else if (falta.length > 0) {
    marcarError(clave, "A la contraseña le falta: " + falta.join(", ") + ".");
    hayErrores = true;
  }

  if (clave2.value === "") {
    marcarError(clave2, "Repite la contraseña.");
    hayErrores = true;
  } else if (clave.value !== clave2.value) {
    marcarError(clave2, "Las dos contraseñas no coinciden.");
    hayErrores = true;
  }

  if (hayErrores) {
    evento.preventDefault();
  }
});

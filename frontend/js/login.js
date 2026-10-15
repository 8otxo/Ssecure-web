/* ══════════════════════════════════════════════════════════════════════════
   VALIDACIÓN DEL FORMULARIO DE ACCESO · clase 03
   ══════════════════════════════════════════════════════════════════════════
   ⚠️ Esto es EXPERIENCIA DE USO, no seguridad. Sirve para que quien se
   equivoca sin querer lo sepa antes de enviar. A quien quiere saltárselo no
   le cuesta nada: lo comprobaréis vosotros mismos en el paso siguiente.
   La validación que cuenta es la del servidor. Siempre.
   ══════════════════════════════════════════════════════════════════════════ */

// Localizamos una sola vez los tres elementos con los que vamos a trabajar.
// querySelector busca en la página: "form" es la etiqueta, "#username" es
// el elemento cuyo id es username.
const formulario = document.querySelector("form");
const usuario    = document.querySelector("#username");
const clave      = document.querySelector("#password");


// ── 1 · Las reglas de la contraseña ──────────────────────────────────────
// Devuelve la LISTA de lo que falta. Vacía = contraseña correcta.
// Devolver una lista y no true/false nos deja decirle al usuario QUÉ falta,
// en vez de un "está mal" que no ayuda a nadie.
//
// Lo de /[a-z]/ es una EXPRESIÓN REGULAR: un patrón de búsqueda.
//   /[a-z]/.test(valor)  →  ¿hay alguna letra minúscula dentro de valor?
//   /[^A-Za-z0-9]/       →  el ^ dentro de los corchetes significa "ninguno
//                            de estos", o sea: algo que no sea letra ni número
function loQueFaltaEnLaClave(valor) {
  const falta = [];                                     // empezamos con la lista vacía
  if (valor.length < 8)            falta.push("8 caracteres");
  if (!/[a-z]/.test(valor))        falta.push("una minúscula");
  if (!/[A-Z]/.test(valor))        falta.push("una mayúscula");
  if (!/[0-9]/.test(valor))        falta.push("un número");
  if (!/[^A-Za-z0-9]/.test(valor)) falta.push("un símbolo");
  return falta;                                         // push() va añadiendo a la lista
}


// ── 2 · Enseñar y quitar el mensaje de error ─────────────────────────────

// PONE el aviso: crea un <p> rojo y lo coloca justo debajo del campo.
function marcarError(campo, mensaje) {
  // Primero limpiamos: si no, al pulsar "Entrar" dos veces seguidas
  // tendríamos el mismo aviso repetido debajo del campo.
  quitarError(campo);

  const aviso = document.createElement("p");
  aviso.className = "error";            // la clase .error está en base.css
  aviso.id = campo.id + "-error";       // p.ej. "password-error", para localizarlo luego
  aviso.textContent = mensaje;          // TEXTO. Nunca innerHTML.

  // aria-invalid marca el campo como erróneo. Sirve para DOS cosas a la vez:
  //   · un lector de pantalla anuncia "inválido" al llegar al campo
  //   · el CSS lo usa para pintar el borde en rojo
  campo.setAttribute("aria-invalid", "true");

  // aria-describedby enlaza el campo con SU mensaje, para que el lector
  // de pantalla no solo diga "inválido", sino que lea también qué pasa.
  campo.setAttribute("aria-describedby", aviso.id);

  campo.after(aviso);                   // el aviso va JUNTO al campo, no en un alert()
}


// QUITA el aviso: deja el campo como si nunca hubiera fallado.
// Hace justo lo contrario que marcarError(), en el mismo orden.
function quitarError(campo) {
  campo.removeAttribute("aria-invalid");      // el borde vuelve a su color
  campo.removeAttribute("aria-describedby");  // se rompe el enlace con el mensaje

  // Y borramos el <p> del aviso, si es que había uno.
  // getElementById devuelve null cuando no existe, por eso el if:
  // llamar a .remove() sobre null daría error.
  const viejo = document.getElementById(campo.id + "-error");
  if (viejo) viejo.remove();
}


// ── 3 · Al enviar ────────────────────────────────────────────────────────
// addEventListener("submit", ...) significa: "cuando alguien envíe este
// formulario, ejecuta esta función". El `evento` que llega como parámetro
// es el envío en sí, y lo necesitamos para poder cancelarlo al final.
formulario.addEventListener("submit", (evento) => {
  let hayErrores = false;              // de momento suponemos que todo está bien

  // Borramos los avisos de la vez anterior. Si no, se quedarían en pantalla
  // mensajes de errores que el usuario ya ha corregido.
  quitarError(usuario);
  quitarError(clave);

  // .value es lo que el usuario ha escrito. .trim() quita los espacios de
  // los lados: así "   " cuenta como vacío, que es lo que queremos.
  if (usuario.value.trim() === "") {
    marcarError(usuario, "Escribe tu usuario.");
    hayErrores = true;
  }

  // En la contraseña NO usamos .trim(): un espacio puede ser parte de la
  // contraseña y no somos nadie para quitárselo.
  if (clave.value === "") {
    marcarError(clave, "Escribe tu contraseña.");
    hayErrores = true;
  }

  // ⚠️ AQUÍ NO SE COMPRUEBA LA FUERZA DE LA CONTRASEÑA. A PROPÓSITO.
  //
  // En el laboratorio lo probamos y pasó esto: admin/admin123 dejó de poder
  // entrar. Su propia validación les cerró la puerta.
  //
  // Y está bien que pasara, porque enseña dónde va cada cosa:
  //   · En el REGISTRO se ELIGE la contraseña  -> ahí sí se exige que sea fuerte
  //   · En el LOGIN la contraseña YA EXISTE    -> aquí solo se comprueba que no
  //     esté vacía, y el servidor dirá si es o no la correcta
  //
  // Además, exigir el formato en el login le REGALA al atacante vuestra
  // política de contraseñas sin que tenga ni que registrarse.
  //
  // Por eso loQueFaltaEnLaClave() está escrita aquí arriba pero no se usa:
  // es la que vais a llevaros a register.js en la tarea.

  if (hayErrores) {
    // Sin esto el navegador enviaría el formulario y recargaría la página,
    // y los mensajes que acabamos de pintar desaparecerían al instante.
    evento.preventDefault();
  }
});

/* ══════════════════════════════════════════════════════════════════════════
   AYUDANTE PARA HABLAR CON LA API · clase 03
   ══════════════════════════════════════════════════════════════════════════
   Todas las vistas del panel piden datos igual, así que la parte repetida
   vive aquí y cada vista solo se ocupa de pintar lo suyo.

   Se carga ANTES que el JavaScript de cada página:
       <script src="/js/api.js"     defer></script>
       <script src="/js/equipo.js"  defer></script>
   Con defer, los scripts se ejecutan en el orden en que aparecen.
   ══════════════════════════════════════════════════════════════════════════ */

/**
 * Pide datos a la API y devuelve la lista que haya dentro.
 *
 * Comprueba TRES cosas, en este orden. Las tres hacen falta:
 *   1 · ¿llegó bien?    -> res.ok. fetch NO falla solo con un 404 ni un 500
 *   2 · ¿es JSON?       -> res.json() revienta si llega otra cosa
 *   3 · ¿tiene forma?   -> que la clave exista y sea una lista
 *
 * El tercero es el que casi nadie escribe, y es el que te salva el día que
 * en el backend renombran un campo: en vez de un "undefined is not iterable"
 * incomprensible, sale un mensaje que dice qué ha pasado.
 */
async function pedirLista(ruta, clave) {
  const res = await fetch(ruta);

  if (!res.ok) {
    throw new Error(`${ruta} respondió ${res.status}`);
  }

  const datos = await res.json();

  if (!Array.isArray(datos[clave])) {
    throw new Error(`${ruta} no devolvió la lista "${clave}" que esperábamos`);
  }

  return datos[clave];
}


/** Igual que pedirLista(), pero para un objeto suelto en vez de una lista. */
async function pedirObjeto(ruta, clave) {
  const res = await fetch(ruta);

  if (!res.ok) {
    throw new Error(`${ruta} respondió ${res.status}`);
  }

  const datos = await res.json();

  if (typeof datos[clave] !== "object" || datos[clave] === null) {
    throw new Error(`${ruta} no devolvió el objeto "${clave}" que esperábamos`);
  }

  return datos[clave];
}


/**
 * Crea una celda de tabla con TEXTO.
 *
 * textContent, nunca innerHTML: lo que llega de la API es un dato, no código.
 * Un nombre de archivo puede traer <img src=x onerror="..."> y con innerHTML
 * eso se ejecutaría. Con textContent se lee como lo que es: texto.
 */
function celda(texto, etiqueta = "td") {
  const c = document.createElement(etiqueta);
  c.textContent = texto;
  return c;
}


/** Una etiqueta de color según el estado. Las clases están en panel.css. */
function etiquetaEstado(estado, estadosBuenos = ["analizado", "completado", "activo"]) {
  const span = document.createElement("span");
  span.textContent = estado;
  span.classList.add("etiqueta");
  span.classList.add(estadosBuenos.includes(estado) ? "etiqueta--ok" : "etiqueta--espera");
  return span;
}


/** Pinta un mensaje de error dentro del <tbody>, ocupando toda la fila. */
function errorEnTabla(cuerpo, columnas, mensaje) {
  cuerpo.replaceChildren();
  const fila = document.createElement("tr");
  const td = celda(mensaje);
  td.colSpan = columnas;
  td.className = "cargando";
  fila.append(td);
  cuerpo.append(fila);
}

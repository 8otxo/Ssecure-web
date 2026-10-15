/* Pinta la tabla de documentos del panel. Usa los ayudantes de api.js.

   OJO AL TERCER DOCUMENTO de la lista: su nombre es una carga de XSS.
   Está ahí a propósito desde la clase 03. Si lo pintas con innerHTML, se
   ejecuta. Con textContent se lee como texto, que es lo que es.           */

async function cargarDocumentos() {
  const cuerpo = document.querySelector("#tabla-documentos");

  try {
    const documentos = await pedirLista("/api/documentos", "documentos");

    cuerpo.replaceChildren();

    for (const doc of documentos) {
      const fila = document.createElement("tr");

      const nombre = celda(doc.nombre, "th");   // celda() usa textContent
      nombre.scope = "row";

      const estado = document.createElement("td");
      estado.append(etiquetaEstado(doc.estado));

      fila.append(nombre, celda(doc.tamano_kb + " KB"), celda(doc.subido), estado);
      cuerpo.append(fila);
    }

    document.querySelector('[data-campo="documentos"]').textContent =
      documentos.length;

  } catch (error) {
    errorEnTabla(cuerpo, 4, "No se pudieron cargar los documentos.");
    console.error(error);
  }
}


/* Un botón que NO está en el HTML: lo crea JavaScript al cargar la página. */
function ponerBotonActualizar() {
  const boton = document.createElement("button");
  boton.type = "button";
  boton.className = "boton";
  boton.textContent = "Actualizar";

  boton.addEventListener("click", () => {
    boton.textContent = "Actualizando...";
    cargarDocumentos().then(() => { boton.textContent = "Actualizar"; });
  });

  document.querySelector(".seccion__cabecera").append(boton);
}


cargarDocumentos();
ponerBotonActualizar();

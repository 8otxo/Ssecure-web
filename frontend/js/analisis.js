/* Pinta la tabla de análisis. Usa los ayudantes de api.js. */

async function cargarAnalisis() {
  const cuerpo = document.querySelector("#tabla-analisis");

  try {
    const analisis = await pedirLista("/api/analisis", "analisis");

    cuerpo.replaceChildren();

    for (const a of analisis) {
      const fila = document.createElement("tr");

      const nombre = celda(a.documento, "th");
      nombre.scope = "row";

      const estado = document.createElement("td");
      estado.append(etiquetaEstado(a.estado));

      fila.append(nombre, celda(a.tipo), celda(a.duracion_s + " s"), estado);
      cuerpo.append(fila);
    }

    document.querySelector('[data-campo="total"]').textContent =
      analisis.length + " en total";

  } catch (error) {
    // Si algo falla, el usuario tiene que enterarse. Un panel vacío sin
    // explicación es peor que un mensaje de error.
    errorEnTabla(cuerpo, 4, "No se pudieron cargar los análisis.");
    console.error(error);
  }
}

cargarAnalisis();

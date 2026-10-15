/* Rellena las tarjetas del plan contratado. */

async function cargarPlan() {
  try {
    const s = await pedirObjeto("/api/suscripcion", "suscripcion");

    const poner = (campo, texto) => {
      document.querySelector(`[data-campo="${campo}"]`).textContent = texto;
    };

    poner("plan", s.plan);
    poner("documentos", s.documentos_usados);
    poner("documentos-pie", "de " + s.documentos_incluidos + " incluidos");
    poner("analisis", s.analisis_usados);
    poner("analisis-pie", "de " + s.analisis_incluidos + " incluidos");
    poner("renovacion", s.renovacion);

  } catch (error) {
    document.querySelector('[data-campo="plan"]').textContent = "error";
    console.error(error);
  }
}

cargarPlan();

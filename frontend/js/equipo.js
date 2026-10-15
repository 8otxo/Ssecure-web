/* Pinta la tabla de usuarios de la organización. */

async function cargarEquipo() {
  const cuerpo = document.querySelector("#tabla-equipo");

  try {
    const usuarios = await pedirLista("/api/usuarios", "usuarios");

    cuerpo.replaceChildren();

    for (const u of usuarios) {
      const fila = document.createElement("tr");

      const nombre = celda(u.nombre, "th");
      nombre.scope = "row";

      const rol = document.createElement("td");
      const insignia = document.createElement("span");
      insignia.textContent = u.rol;
      insignia.className = "rol rol--tabla";
      rol.append(insignia);

      const estado = document.createElement("td");
      estado.append(etiquetaEstado(u.estado));

      fila.append(nombre, celda(u.correo), rol, celda(u.alta), estado);
      cuerpo.append(fila);
    }

    document.querySelector('[data-campo="total"]').textContent =
      usuarios.length + " personas";

  } catch (error) {
    errorEnTabla(cuerpo, 5, "No se pudieron cargar los usuarios.");
    console.error(error);
  }
}

cargarEquipo();

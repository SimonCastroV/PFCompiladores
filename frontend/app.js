// --- Referencias a elementos del DOM ---
const btnProcesar = document.getElementById("btnProcesar");
const btnProbarLL1 = document.getElementById("btnProbarLL1");
const btnProbarSLR1 = document.getElementById("btnProbarSLR1");
const gramText = document.getElementById("gramText");
const cadenaInput = document.getElementById("cadena");
const btnLimpiar = document.getElementById("btnLimpiar");

const msg = document.getElementById("msg");
const gramNorm = document.getElementById("gramNorm");
const primerosDiv = document.getElementById("primeros");
const siguientesDiv = document.getElementById("siguientes");
const propsDiv = document.getElementById("props");
const resultadoDiv = document.getElementById("resultado");
const tablasDiv = document.getElementById("tablas");

const resultsPanel = document.getElementById("results");

// --- Variables globales ---
let ultimaGramatica = "";
let datosAnalisis = null;

// --- URL base del backend ---
const API_URL = "http://127.0.0.1:8000/api/analizar";

// --- Función de ayuda para mostrar mensajes animados ---
function showMessage(text, type = "info") {
  msg.textContent = text;
  msg.className = `msg ${type}`;
  msg.style.opacity = 1;
  setTimeout(() => (msg.style.opacity = 0.9), 150);
}

// --- Animación simple para elementos nuevos ---
function animateElement(el) {
  el.style.opacity = 0;
  el.style.transform = "translateY(10px)";
  setTimeout(() => {
    el.style.transition = "all 0.3s ease";
    el.style.opacity = 1;
    el.style.transform = "translateY(0)";
  }, 100);
}

// --- Mostrar resultados en pantalla ---
function renderResultados(data) {
  const pretty = (s) => (s === "e" ? "ε" : s);
  resultsPanel.setAttribute("aria-hidden", "false");

  // Gramática
  gramNorm.textContent = data.gramatica || "";

  // --- PRIMEROS (orden preservado y color único) ---
  primerosDiv.innerHTML = "";

  // ✅ Obtener el orden original de los no terminales desde la gramática normalizada
  const ordenNoTerminales = [];
  (data.gramatica || "")
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.includes("->"))
    .forEach((l) => {
      const nt = l.split("->")[0].trim();
      if (!ordenNoTerminales.includes(nt)) ordenNoTerminales.push(nt);
    });

  // ✅ Iterar respetando ese orden
  ordenNoTerminales.forEach((simbolo) => {
    const valores = data.primeros[simbolo];
    if (!valores) return;
    const p = document.createElement("p");
    p.innerHTML = `<strong class="symbol">${simbolo}</strong> → { ${valores
      .map(pretty)
      .join(", ")} }`;
    primerosDiv.appendChild(p);
    animateElement(p);
  });

  // --- SIGUIENTES (mismo orden y color unificado) ---
  siguientesDiv.innerHTML = "";
  ordenNoTerminales.forEach((simbolo) => {
    const valores = data.siguientes[simbolo];
    if (!valores) return;
    const p = document.createElement("p");
    p.innerHTML = `<strong class="symbol">${simbolo}</strong> → { ${valores
      .map(pretty)
      .join(", ")} }`;
    siguientesDiv.appendChild(p);
    animateElement(p);
  });

  // --- Propiedades generales ---
  propsDiv.innerHTML = "";
  const alerta = document.createElement("div");
  alerta.className = "alerta-global";

  if (!data.es_ll1 && !data.es_slr1) {
    alerta.innerHTML = `
      <span class="icono">⚠️</span>
      <div>
        <strong>La gramática no es determinista.</strong><br>
        Presenta conflictos en <b>LL(1)</b> y <b>SLR(1)</b>; no puede analizarse por métodos predictivos ni bottom-up sin resolver ambigüedades.
      </div>`;
    alerta.classList.add("alerta-roja");
  } else if (!data.es_ll1 && data.es_slr1) {
    alerta.innerHTML = `
      <span class="icono">ℹ️</span>
      <div>
        <strong>La gramática no es LL(1).</strong><br>
        Sin embargo, es <b>SLR(1)</b>, por lo que puede analizarse correctamente con un enfoque bottom-up.
      </div>`;
    alerta.classList.add("alerta-amarilla");
  } else if (data.es_ll1 && !data.es_slr1) {
    alerta.innerHTML = `
      <span class="icono">ℹ️</span>
      <div>
        <strong>La gramática no es SLR(1).</strong><br>
        Es <b>LL(1)</b>, por lo tanto puede analizarse predictivamente.
      </div>`;
    alerta.classList.add("alerta-amarilla");
  } else {
    alerta.innerHTML = `
      <span class="icono">✅</span>
      <div>
        <strong>Gramática determinista.</strong><br>
        Es válida tanto para análisis <b>LL(1)</b> como <b>SLR(1)</b>.
      </div>`;
    alerta.classList.add("alerta-verde");
  }

  propsDiv.appendChild(alerta);

  // --- Detalle de conflictos ---
  const ll1Info = document.createElement("div");
  ll1Info.innerHTML = `<p>Es LL(1): ${data.es_ll1 ? "✅" : "❌"}</p>`;
  if (!data.es_ll1 && data.detalle_ll1) {
    const err = document.createElement("div");
    err.className = "alerta-conflicto";
    err.innerHTML = `<span class="icono">⚠️</span> <strong>Conflicto LL(1):</strong> ${data.detalle_ll1
      .replace("Conflicto LL(1):", "")
      .trim()}`;
    ll1Info.appendChild(err);
  }

  const slr1Info = document.createElement("div");
  slr1Info.innerHTML = `<p>Es SLR(1): ${data.es_slr1 ? "✅" : "❌"}</p>`;
  if (!data.es_slr1 && data.detalle_slr1) {
    const err = document.createElement("div");
    err.className = "alerta-conflicto";
    err.innerHTML = `<span class="icono">⚠️</span> <strong>Conflicto SLR(1):</strong> ${data.detalle_slr1
      .replace("Conflicto SLR(1):", "")
      .trim()}`;
    slr1Info.appendChild(err);
  }

  propsDiv.appendChild(ll1Info);
  propsDiv.appendChild(slr1Info);

  // Tablas
  tablasDiv.innerHTML = "";

  // ====== TABLA LL(1) ======
  if (data.es_ll1 && data.tabla_ll1) {
    const cont = document.createElement("div");
    cont.innerHTML = `<h4>Tabla LL(1)</h4>`;
    const table = document.createElement("table");
    table.className = "tabla-analisis";

    // Recolectar terminales únicos
    const terminalesSet = new Set();
    Object.values(data.tabla_ll1).forEach((fila) =>
      Object.keys(fila).forEach((t) => terminalesSet.add(t))
    );

    // Orden canónico según Aho et al. (id, (, ), *, +, $)
    const ordenCanonico = ["id", "+", "*", "(", ")", "$"];

    // Si hay terminales adicionales en la gramática, los añadimos al final ordenados alfabéticamente
    const terminalesDetectados = Array.from(terminalesSet);
    const terminales = terminalesDetectados.sort((a, b) => {
      const ia = ordenCanonico.indexOf(a);
      const ib = ordenCanonico.indexOf(b);

      // Ambos no están en el orden canónico → orden alfabético
      if (ia === -1 && ib === -1) return a.localeCompare(b);

      // Uno está en el orden canónico → priorizarlo
      if (ia === -1) return 1;
      if (ib === -1) return -1;

      // Ambos están en el orden canónico → seguir ese orden
      return ia - ib;
    });

    // Cabecera
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    headRow.innerHTML =
      `<th>No terminal</th>` + terminales.map((t) => `<th>${t}</th>`).join("");
    thead.appendChild(headRow);
    table.appendChild(thead);

    // Filas
    const tbody = document.createElement("tbody");
    ordenNoTerminales.forEach((nt) => {
      const fila = data.tabla_ll1[nt];
      if (!fila) return;
      const tr = document.createElement("tr");
      let html = `<td><strong>${nt}</strong></td>`;
      terminales.forEach((t) => {
        const produccion = fila[t];
        let celda = "";
        if (produccion)
          celda = produccion.length === 0 ? "ε" : produccion.join(" ");
        html += `<td>${celda}</td>`;
      });
      tr.innerHTML = html;
      tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    cont.appendChild(table);
    tablasDiv.appendChild(cont);
  }

  // ====== TABLA SLR(1) ======
  if (data.es_slr1 && data.tabla_slr_action) {
    const cont = document.createElement("div");
    cont.innerHTML = `<h4>Tabla ACTION / GOTO (SLR)</h4>`;
    const table = document.createElement("table");
    table.className = "tabla-analisis";

    // === ORDEN CANÓNICO DE AHO ===
    const ordenCanonicoTerm = ["id", "+", "*", "(", ")", "$"];

    // === ORDEN DE NO TERMINALES SEGÚN GRAMÁTICA ===
    const ordenNoTerm = [];
    (data.gramatica || "")
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter((l) => l.includes("->"))
      .forEach((l) => {
        const nt = l.split("->")[0].trim();
        if (!ordenNoTerm.includes(nt)) ordenNoTerm.push(nt);
      });

    // === DETECTAR TERMINALES Y NO TERMINALES ===
    const estados = Object.keys(data.tabla_slr_action);
    const terminalesSet = new Set(ordenCanonicoTerm);
    Object.values(data.tabla_slr_action).forEach((fila) =>
      Object.keys(fila).forEach((t) => terminalesSet.add(t))
    );

    const terminales = Array.from(terminalesSet).sort((a, b) => {
      const ia = ordenCanonicoTerm.indexOf(a);
      const ib = ordenCanonicoTerm.indexOf(b);
      if (ia === -1 && ib === -1) return a.localeCompare(b);
      if (ia === -1) return 1;
      if (ib === -1) return -1;
      return ia - ib;
    });

    // === CABECERA EN DOS NIVELES (ACTION / GOTO) ===
    const thead = document.createElement("thead");

    // Fila 1: encabezados de secciones
    const rowTop = document.createElement("tr");
    rowTop.innerHTML =
      `<th rowspan="2">STATE</th>` +
      `<th colspan="${terminales.length}">ACTION</th>` +
      `<th colspan="${ordenNoTerm.length}">GOTO</th>`;
    thead.appendChild(rowTop);

    // Fila 2: encabezados de símbolos
    const rowBottom = document.createElement("tr");
    rowBottom.innerHTML =
      terminales.map((t) => `<th>${t}</th>`).join("") +
      ordenNoTerm.map((nt) => `<th>${nt}</th>`).join("");
    thead.appendChild(rowBottom);

    table.appendChild(thead);

    // === CUERPO DE LA TABLA ===
    const tbody = document.createElement("tbody");
    estados.forEach((est) => {
      const tr = document.createElement("tr");
      let html = `<td><strong>${est}</strong></td>`;

      // ACTION (terminales)
      terminales.forEach((t) => {
        const accion = data.tabla_slr_action[est]?.[t];
        let valor = "";
        if (accion) {
          const tipo = accion[0];
          if (tipo.startsWith("shift")) {
            valor = "s" + (accion[1] !== undefined ? accion[1] : "");
          } else if (tipo.startsWith("reduce")) {
            valor = "r" + (accion[1] !== undefined ? accion[1] : "");
          } else if (tipo === "accept") {
            valor = "acc";
          }
        }
        html += `<td>${valor}</td>`;
      });

      // GOTO (no terminales)
      ordenNoTerm.forEach((nt) => {
        const goto = data.tabla_slr_goto?.[est]?.[nt];
        html += `<td>${goto !== undefined ? goto : ""}</td>`;
      });

      tr.innerHTML = html;
      tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    cont.appendChild(table);
    tablasDiv.appendChild(cont);
  }
}

// --- Evento: Procesar gramática ---
if (btnProcesar) {
  btnProcesar.addEventListener("click", async () => {
    const texto = gramText.value.trim();
    if (!texto) {
      showMessage("Por favor, ingresa una gramática.", "error");
      return;
    }

    showMessage("Procesando gramática...", "info");
    resultadoDiv.textContent = "";

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ gramatica: texto }),
      });

      const data = await res.json();
      if (res.ok) {
        datosAnalisis = data;
        ultimaGramatica = texto;
        renderResultados(data);
        showMessage("✅ Gramática procesada correctamente.", "success");
      } else {
        let mensaje = data.error || "Error desconocido";
        if (mensaje.toLowerCase().startsWith("error")) {
          showMessage(mensaje, "error");
        } else {
          showMessage("Error: " + mensaje, "error");
        }
      }
    } catch (err) {
      console.error(err);
      showMessage("Error de conexión con la API.", "error");
    }
  });
}

// --- Función para probar una cadena ---
async function probarCadena(tipo) {
  const cadena = cadenaInput.value.trim();
  if (!cadena) {
    showMessage("Escribe una cadena antes de probar.", "error");
    return;
  }
  if (!ultimaGramatica) {
    showMessage("Primero procesa la gramática.", "error");
    return;
  }

  showMessage("Analizando cadena...", "info");

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        gramatica: ultimaGramatica,
        cadena: cadena,
      }),
    });

    const data = await res.json();
    if (res.ok) {
      let aceptado = false;
      if (tipo === "ll1") aceptado = data.aceptada_ll1;
      else aceptado = data.aceptada_slr1;

      resultadoDiv.innerHTML = `
        <p class="result-text ${aceptado ? "ok" : "fail"}">${
        aceptado ? "✅ Cadena aceptada" : "❌ Cadena rechazada"
      }</p>
      `;
      animateElement(resultadoDiv);

      // ✅ Aquí sí existe "data", así que la simulación funcionará
      if (tipo === "slr1" && data.es_slr1) {
        iniciarSimulacion(data);
      }
    } else {
      let mensaje = data.error || "Error desconocido";
      if (mensaje.toLowerCase().startsWith("error")) {
        showMessage(mensaje, "error");
      } else {
        showMessage("Error: " + mensaje, "error");
      }
    }
  } catch (err) {
    console.error(err);
    showMessage("Error de conexión con la API.", "error");
  }
}

// --- Eventos para los botones de prueba ---
if (btnProbarLL1) {
  btnProbarLL1.addEventListener("click", () => probarCadena("ll1"));
}
if (btnProbarSLR1) {
  btnProbarSLR1.addEventListener("click", () => probarCadena("slr1"));
}

// --- Evento: Limpiar todo ---
if (btnLimpiar) {
  btnLimpiar.addEventListener("click", () => {
    // Limpiar todos los campos y resultados
    gramText.value = "";
    cadenaInput.value = "";
    msg.textContent = "";
    resultadoDiv.textContent = "";
    gramNorm.textContent = "";
    primerosDiv.innerHTML = "";
    siguientesDiv.innerHTML = "";
    propsDiv.innerHTML = "";
    tablasDiv.innerHTML = "";

    // Ocultar panel de resultados
    resultsPanel.setAttribute("aria-hidden", "true");

    // Reiniciar variables globales
    ultimaGramatica = "";
    datosAnalisis = null;

    // Mostrar mensaje informativo
    showMessage(
      " Campos limpiados. Puedes ingresar una nueva gramática.",
      "info"
    );
  });
}
// --- Referencias a elementos del DOM ---
const btnProcesar = document.getElementById("btnProcesar");
const btnProbarLL1 = document.getElementById("btnProbarLL1");
const btnProbarSLR1 = document.getElementById("btnProbarSLR1");
const gramText = document.getElementById("gramText");
const cadenaInput = document.getElementById("cadena");

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
  resultsPanel.setAttribute("aria-hidden", "false");

  // Gramática
  gramNorm.textContent = data.gramatica || "";

  // --- Primeros ---
  primerosDiv.innerHTML = "";
  for (const [nt, valores] of Object.entries(data.primeros)) {
    if (nt === "$") continue; // 👈 oculta FIRST($)
    const p = document.createElement("p");
    p.innerHTML = `<strong>${nt}</strong> → { ${valores.join(", ")} }`;
    primerosDiv.appendChild(p);
    animateElement(p);
  }

  // --- Siguientes ---
  siguientesDiv.innerHTML = "";
  for (const [nt, valores] of Object.entries(data.siguientes)) {
    if (nt === "$") continue; // 👈 evita mostrar FOLLOW($)
    const p = document.createElement("p");
    p.innerHTML = `<strong>${nt}</strong> → { ${valores.join(", ")} }`;
    siguientesDiv.appendChild(p);
    animateElement(p);
  }

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
    err.innerHTML = `<span class="icono">⚠️</span> <strong>Conflicto LL(1):</strong> ${data.detalle_ll1.replace("Conflicto LL(1):", "").trim()}`;
    ll1Info.appendChild(err);
  }

  const slr1Info = document.createElement("div");
  slr1Info.innerHTML = `<p>Es SLR(1): ${data.es_slr1 ? "✅" : "❌"}</p>`;
  if (!data.es_slr1 && data.detalle_slr1) {
    const err = document.createElement("div");
    err.className = "alerta-conflicto";
    err.innerHTML = `<span class="icono">⚠️</span> <strong>Conflicto SLR(1):</strong> ${data.detalle_slr1.replace("Conflicto SLR(1):", "").trim()}`;
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

    // Obtener todos los terminales únicos
    const terminales = new Set();
    Object.values(data.tabla_ll1).forEach((fila) =>
      Object.keys(fila).forEach((t) => terminales.add(t))
    );

    // Cabecera
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    headRow.innerHTML =
      `<th>No terminal</th>` +
      Array.from(terminales)
        .map((t) => `<th>${t}</th>`)
        .join("");
    thead.appendChild(headRow);
    table.appendChild(thead);

    // Filas
    const tbody = document.createElement("tbody");
    Object.entries(data.tabla_ll1).forEach(([nt, fila]) => {
      const tr = document.createElement("tr");
      let html = `<td><strong>${nt}</strong></td>`;
      Array.from(terminales).forEach((t) => {
        const regla = fila[t] ? fila[t].join(" ") : "";
        html += `<td>${regla}</td>`;
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

    // Determinar terminales y no terminales
    const estados = Object.keys(data.tabla_slr_action);
    const terminales = new Set();
    const noTerminales = new Set();
    Object.values(data.tabla_slr_action).forEach((fila) =>
      Object.keys(fila).forEach((s) => terminales.add(s))
    );
    Object.values(data.tabla_slr_goto || {}).forEach((fila) =>
      Object.keys(fila).forEach((nt) => noTerminales.add(nt))
    );

    // Cabecera combinada
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    headRow.innerHTML =
      `<th>Estado</th>` +
      Array.from(terminales)
        .map((t) => `<th>${t}</th>`)
        .join("") +
      Array.from(noTerminales)
        .map((nt) => `<th>${nt}</th>`)
        .join("");
    thead.appendChild(headRow);
    table.appendChild(thead);

    // Filas con ACTION y GOTO
    const tbody = document.createElement("tbody");
    estados.forEach((est) => {
      const tr = document.createElement("tr");
      let html = `<td><strong>${est}</strong></td>`;
      Array.from(terminales).forEach((t) => {
        const accion = data.tabla_slr_action[est]?.[t];
        html += `<td>${accion ? accion.join(" ") : ""}</td>`;
      });
      Array.from(noTerminales).forEach((nt) => {
        const goto = data.tabla_slr_goto[est]?.[nt];
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

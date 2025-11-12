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
const ordenCanonicoTerm = ["id", "+", "*", "(", ")", "$"];

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

  // --- PRIMEROS (estilo libro y agrupados) ---
  primerosDiv.innerHTML = "";

  const ordenNoTerminales = [];
  (data.gramatica || "")
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.includes("->"))
    .forEach((l) => {
      const nt = l.split("->")[0].trim();
      if (!ordenNoTerminales.includes(nt)) ordenNoTerminales.push(nt);
  });

  if (data.primeros && Object.keys(data.primeros).length > 0) {
    const pretty = (s) => (s === "e" ? "ε" : s);
    const grupos = {};

    // Agrupar los no terminales que comparten el mismo conjunto de primeros
    ordenNoTerminales.forEach((simbolo) => {
      const valores = data.primeros[simbolo];
      if (!valores) return;
      const key = valores.map(pretty).join(", ");
      if (!grupos[key]) grupos[key] = [];
      grupos[key].push(simbolo);
    });

    // Crear el texto agrupado en formato tipo libro
    let textoFirst = "";
    for (const [key, simbolos] of Object.entries(grupos)) {
      textoFirst += simbolos
        .map((s, i) => (i === 0 ? `FIRST(${s})` : ` = FIRST(${s})`))
        .join("");
      textoFirst += ` = { ${key} }\n`;
    }

    // Mostrar el bloque de resultado
    const pre = document.createElement("pre");
    pre.className = "resultado-texto";
    pre.textContent = textoFirst.trim();
    primerosDiv.appendChild(pre);
  }

  // --- SIGUIENTES (orden tipo libro: *, +, ), $) ---
  siguientesDiv.innerHTML = "";
  if (data.siguientes && Object.keys(data.siguientes).length > 0) {
    let textoFollow = "";

    const grupos = {};
    ordenNoTerminales.forEach((simbolo) => {
      const valores = data.siguientes[simbolo];
      if (!valores) return;

      // --- Orden tipo libro ---
      const ordenCanonico = ["*", "+", ")", "$"];
      const restantes = valores.filter((v) => !ordenCanonico.includes(v)).sort();
      const ordenados = [
        ...ordenCanonico.filter((x) => valores.includes(x)),
        ...restantes
      ];

      const key = ordenados.map((s) => (s === "e" ? "ε" : s)).join(", ");
      if (!grupos[key]) grupos[key] = [];
      grupos[key].push(simbolo);
    });

    for (const [key, simbolos] of Object.entries(grupos)) {
      textoFollow += simbolos
        .map((s) => `FOLLOW(${s})`)
        .join(" = ");
      textoFollow += ` = { ${key} }\n`;
    }

    const pre = document.createElement("pre");
    pre.className = "resultado-texto";
    pre.textContent = textoFollow.trim();
    siguientesDiv.appendChild(pre);
  }

  // --- Propiedades ---
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

  // --- Tablas ---
  tablasDiv.innerHTML = "";

  // ====== TABLA LL(1) ======
  if (data.es_ll1 && data.tabla_ll1) {
    const cont = document.createElement("div");
    cont.innerHTML = `<h4>Tabla LL(1)</h4>`;
    const table = document.createElement("table");
    table.className = "tabla-analisis";

    const terminalesSet = new Set();
    Object.values(data.tabla_ll1).forEach((fila) =>
      Object.keys(fila).forEach((t) => terminalesSet.add(t))
    );

    const ordenCanonico = ["id", "+", "*", "(", ")", "$"];
    const terminalesDetectados = Array.from(terminalesSet);
    const terminales = terminalesDetectados.sort((a, b) => {
      const ia = ordenCanonico.indexOf(a);
      const ib = ordenCanonico.indexOf(b);
      if (ia === -1 && ib === -1) return a.localeCompare(b);
      if (ia === -1) return 1;
      if (ib === -1) return -1;
      return ia - ib;
    });

    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    headRow.innerHTML =
      `<th>No terminal</th>` + terminales.map((t) => `<th>${t}</th>`).join("");
    thead.appendChild(headRow);
    table.appendChild(thead);

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

    const ordenCanonicoTerm = ["id", "+", "*", "(", ")", "$"];
    const ordenNoTerm = ordenNoTerminales;

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

    const thead = document.createElement("thead");
    const rowTop = document.createElement("tr");
    rowTop.innerHTML =
      `<th rowspan="2">STATE</th>` +
      `<th colspan="${terminales.length}">ACTION</th>` +
      `<th colspan="${ordenNoTerm.length}">GOTO</th>`;
    thead.appendChild(rowTop);

    const rowBottom = document.createElement("tr");
    rowBottom.innerHTML =
      terminales.map((t) => `<th>${t}</th>`).join("") +
      ordenNoTerm.map((nt) => `<th>${nt}</th>`).join("");
    thead.appendChild(rowBottom);

    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    estados.forEach((est) => {
      const tr = document.createElement("tr");
      let html = `<td><strong>${est}</strong></td>`;

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
        showMessage("Error: " + (data.error || "Error desconocido"), "error");
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
      const aceptado =
        tipo === "ll1" ? data.aceptada_ll1 : data.aceptada_slr1;

      resultadoDiv.innerHTML = `
        <p class="result-text ${aceptado ? "ok" : "fail"}">${
        aceptado ? "✅ Cadena aceptada" : "❌ Cadena rechazada"
      }</p>`;
      animateElement(resultadoDiv);

      if (tipo === "slr1" && data.es_slr1) {
        iniciarSimulacion(data);
      }
    } else {
      showMessage("Error: " + (data.error || "Error desconocido"), "error");
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
    gramText.value = "";
    cadenaInput.value = "";
    msg.textContent = "";
    resultadoDiv.textContent = "";
    gramNorm.textContent = "";
    primerosDiv.innerHTML = "";
    siguientesDiv.innerHTML = "";
    propsDiv.innerHTML = "";
    tablasDiv.innerHTML = "";
    resultsPanel.setAttribute("aria-hidden", "true");
    ultimaGramatica = "";
    datosAnalisis = null;
    showMessage("Campos limpiados. Puedes ingresar una nueva gramática.", "info");
  });
}

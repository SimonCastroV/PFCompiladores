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

  // Primeros
  primerosDiv.innerHTML = "";
  for (const [nt, valores] of Object.entries(data.primeros)) {
    const p = document.createElement("p");
    p.innerHTML = `<strong>${nt}</strong> → { ${valores.join(", ")} }`;
    primerosDiv.appendChild(p);
    animateElement(p);
  }

  // Siguientes
  siguientesDiv.innerHTML = "";
  for (const [nt, valores] of Object.entries(data.siguientes)) {
    const p = document.createElement("p");
    p.innerHTML = `<strong>${nt}</strong> → { ${valores.join(", ")} }`;
    siguientesDiv.appendChild(p);
    animateElement(p);
  }

  // Propiedades
  propsDiv.innerHTML = `
    <p>Es LL(1): ${data.es_ll1 ? "✅" : "❌"}</p>
    <p>Es SLR(1): ${data.es_slr1 ? "✅" : "❌"}</p>
  `;

  // Tablas
  tablasDiv.innerHTML = "";
  if (data.es_ll1 && data.tabla_ll1) {
    const tabla = document.createElement("div");
    tabla.innerHTML = `<h4>Tabla LL(1)</h4>`;
    for (const [nt, fila] of Object.entries(data.tabla_ll1)) {
      const filaTxt = Object.entries(fila)
        .map(([k, v]) => `${k}: [${v.join(", ")}]`)
        .join("; ");
      const p = document.createElement("p");
      p.textContent = `${nt} → ${filaTxt}`;
      tabla.appendChild(p);
    }
    tablasDiv.appendChild(tabla);
  }

  if (data.es_slr1 && data.tabla_slr_action) {
    const tabla = document.createElement("div");
    tabla.innerHTML = `<h4>Tabla ACTION (SLR)</h4>`;
    Object.entries(data.tabla_slr_action).forEach(([i, fila]) => {
      const p = document.createElement("p");
      p.textContent = `Estado ${i}: ${JSON.stringify(fila)}`;
      tabla.appendChild(p);
    });
    tablasDiv.appendChild(tabla);
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
      let aceptado = false;
      if (tipo === "ll1") aceptado = data.aceptada_ll1;
      else aceptado = data.aceptada_slr1;

      resultadoDiv.innerHTML = `
        <p class="result-text ${
          aceptado ? "ok" : "fail"
        }">${aceptado ? "✅ Cadena aceptada" : "❌ Cadena rechazada"}</p>
      `;
      animateElement(resultadoDiv);

      // ✅ Aquí sí existe "data", así que la simulación funcionará
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
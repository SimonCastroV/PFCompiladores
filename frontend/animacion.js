let pasos = [];
let pasoActual = 0;

const pilaDiv = document.getElementById("pila");
const entradaDiv = document.getElementById("entrada");
const accionDiv = document.getElementById("accion");
const btnPaso = document.getElementById("btnPaso");
const simulador = document.getElementById("simulador");

function iniciarSimulacion(data) {
  simulador.setAttribute("aria-hidden", "false");
  pilaDiv.textContent = "[0]";
  entradaDiv.textContent = (data.cadena || "") + "$";
  accionDiv.textContent = "Esperando acción...";
  pasos = generarPasos(data);
  pasoActual = 0;
  btnPaso.disabled = false;

  if (pasos.length === 0) {
    accionDiv.textContent = "No se pudo simular esta gramática (faltan tablas).";
    btnPaso.disabled = true;
  }
}

/**
 * Genera los pasos de simulación del análisis SLR(1)
 * usando las tablas ACTION y GOTO devueltas por la API.
 */
function generarPasos(data) {
  const action = data.tabla_slr_action || {};
  const goto = data.tabla_slr_goto || {};
  const cadena = (data.cadena || "") + "$";
  const pila = [0];
  let i = 0;
  const secuencia = [];

  while (true) {
    const estado = pila[pila.length - 1];
    const simbolo = cadena[i];
    const accion = action[estado]?.[simbolo];

    if (!accion) {
      secuencia.push({
        pila: [...pila],
        entrada: cadena.slice(i),
        accion: `❌ Error: no hay acción para (${estado}, ${simbolo})`
      });
      break;
    }

    const [tipo, valor] = accion;
    let texto = `${tipo.toUpperCase()} ${valor !== null ? valor : ""}`;
    secuencia.push({
      pila: [...pila],
      entrada: cadena.slice(i),
      accion: texto
    });

    if (tipo === "shift") {
      pila.push(simbolo);
      pila.push(valor);
      i++;
    } else if (tipo === "reduce") {
      const [A, beta] = valor;
      if (beta.length > 0) pila.splice(pila.length - 2 * beta.length);
      const t = pila[pila.length - 1];
      const sig = goto[t]?.[A];
      if (sig === undefined) {
        secuencia.push({
          pila: [...pila],
          entrada: cadena.slice(i),
          accion: `❌ Error en GOTO(${t}, ${A})`
        });
        break;
      }
      pila.push(A);
      pila.push(sig);
    } else if (tipo === "accept") {
      secuencia.push({
        pila: [...pila],
        entrada: "$",
        accion: "✅ Cadena aceptada"
      });
      break;
    }
    if (secuencia.length > 50) break; // seguridad
  }

  return secuencia;
}

// --- Control paso a paso ---
if (btnPaso) {
  btnPaso.addEventListener("click", () => {
    if (pasoActual >= pasos.length) {
      accionDiv.textContent = "Simulación terminada.";
      btnPaso.disabled = true;
      return;
    }

    const p = pasos[pasoActual];
    pilaDiv.textContent = p.pila.join(" ");
    entradaDiv.textContent = p.entrada;
    accionDiv.textContent = p.accion;

    [pilaDiv, entradaDiv, accionDiv].forEach(el => {
      el.classList.remove("highlight");
      setTimeout(() => el.classList.add("highlight"), 100);
    });

    pasoActual++;
  });
}

window.iniciarSimulacion = iniciarSimulacion;
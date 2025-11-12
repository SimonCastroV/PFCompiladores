from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os, re

# --- Importar módulos ---
from gramatica import Gramatica
from primeros_siguientes import CalculadorPrimerosSiguientes
from analizador_ll1 import AnalizadorLL1
from analizador_slr1 import AnalizadorSLR1


# -------------------------------------------------
# Configuración de la app
# -------------------------------------------------
app = FastAPI(title="API de Análisis de Gramáticas", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Servir el frontend
# -------------------------------------------------
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

@app.get("/")
def root():
    return FileResponse(os.path.join(frontend_path, "index.html"))


# -------------------------------------------------
# Función auxiliar: parser de texto con validaciones
# -------------------------------------------------
def parsear_gramatica(texto: str):
    """
    Convierte el texto de la gramática en un diccionario estructurado.
    Soporta:
      - Alternativas con '|'
      - Tokens multicaracter como id
      - Epsilon representado por 'e'
      - No terminales sin espacios
    """
    if not texto.strip():
        raise ValueError("La gramática está vacía. Ingresa al menos una producción.")

    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    producciones = {}

    for i, linea in enumerate(lineas, start=1):
        if "->" not in linea:
            raise ValueError(f"Línea {i}: falta '->' en '{linea}'")

        partes = linea.split("->", 1)
        if len(partes) != 2:
            raise ValueError(f"Línea {i}: formato incorrecto en '{linea}'")

        lhs, rhs = partes
        lhs, rhs = lhs.strip(), rhs.strip()

        if not lhs:
            raise ValueError(f"Línea {i}: no se encontró el lado izquierdo.")
        if not rhs:
            raise ValueError(f"Línea {i}: no hay producciones después de '->'.")

        if " " in lhs:
            raise ValueError(f"Línea {i}: el no terminal '{lhs}' no debe contener espacios.")

        if not re.match(r"^[A-Za-z0-9_'\(\)\+\*\-]*$", lhs):
            raise ValueError(f"Línea {i}: el no terminal '{lhs}' contiene caracteres inválidos.")

        alternativas = [alt.strip() for alt in rhs.split("|") if alt.strip()]
        if not alternativas:
            raise ValueError(f"Línea {i}: no se encontraron alternativas.")

        if lhs not in producciones:
            producciones[lhs] = []

        for alt in alternativas:
            if alt == "e":
                producciones[lhs].append([])  # epsilon
            else:
                # Tokenización flexible
                if " " in alt:
                    tokens = alt.split()
                else:
                    TOKEN_RE = re.compile(r"id|[A-Za-z]+'|[A-Za-z]+|[()+*]|\$|ε|e")
                    tokens = TOKEN_RE.findall(alt.strip())

                if not tokens:
                    raise ValueError(f"Línea {i}: la alternativa '{alt}' está vacía o mal formada.")

                producciones[lhs].append(tokens)

    # Validar duplicados
    for lhs, rhs_list in producciones.items():
        vistos = set()
        for rhs in rhs_list:
            cadena = " ".join(rhs)
            if cadena in vistos:
                raise ValueError(f"Producción duplicada detectada: {lhs} -> {cadena}")
            vistos.add(cadena)

    return producciones


# -------------------------------------------------
# Endpoint principal
# -------------------------------------------------
@app.post("/api/analizar")
async def analizar_gramatica(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Error al leer el cuerpo JSON."})

    texto_gramatica = data.get("gramatica", "")
    cadena = data.get("cadena", "")

    if not texto_gramatica:
        return JSONResponse(status_code=400, content={"error": "No se recibió ninguna gramática."})

    try:
        dict_prod = parsear_gramatica(texto_gramatica)
        g = Gramatica(dict_prod)

        # Calcular FIRST y FOLLOW
        calc = CalculadorPrimerosSiguientes(g)
        primeros = calc.calcular_primeros()
        siguientes = calc.calcular_siguientes()

        # Crear analizadores LL(1) y SLR(1)
        ll1 = AnalizadorLL1(g, primeros, siguientes)
        slr1 = AnalizadorSLR1(g, primeros, siguientes)

        # Filtrar solo no terminales
        primeros_filtrados = {
            nt: sorted(list(v - {'$'}))
            for nt, v in primeros.items() if nt in g.no_terminales
        }
        siguientes_filtrados = {
            nt: sorted(list(v - {'e', 'ε'}))
            for nt, v in siguientes.items() if nt in g.no_terminales
        }

        resultado = {
            "gramatica": str(g),
            "no_terminales": sorted(list(g.no_terminales)),
            "terminales": sorted(list(g.terminales - {'$', 'e', 'ε'})),
            "primeros": primeros_filtrados,
            "siguientes": siguientes_filtrados,
            "es_ll1": ll1.es_ll1(),
            "es_slr1": slr1.es_slr1(),
            "tabla_ll1": ll1.tabla_analisis if ll1.es_ll1() else {},
            "tabla_slr_action": getattr(slr1, "tabla_action", {}),
            "tabla_slr_goto": getattr(slr1, "tabla_goto", {}),
            "cadena": cadena,
            "aceptada_ll1": None,
            "aceptada_slr1": None,
            "detalle_ll1": getattr(ll1, "error_conflicto", None),
            "detalle_slr1": getattr(slr1, "error_conflicto", None),
        }

        # Analizar la cadena si existe
        if cadena:
            entrada = cadena if cadena.endswith('$') else cadena + '$'
            try:
                if ll1.es_ll1():
                    resultado["aceptada_ll1"] = ll1.analizar(entrada)
            except Exception as e:
                resultado["aceptada_ll1"] = f"Error: {e}"

            try:
                if slr1.es_slr1():
                    resultado["aceptada_slr1"] = slr1.analizar(entrada)
            except Exception as e:
                resultado["aceptada_slr1"] = f"Error: {e}"

        return JSONResponse(content=resultado)

    except Exception as e:
        mensaje = str(e)
        if mensaje.lower().startswith("error"):
            mensaje = mensaje[6:].strip()
        return JSONResponse(status_code=400, content={"error": f"Error {mensaje}"})


@app.get("/api/test")
def test():
    return {"mensaje": "API funcionando correctamente"}

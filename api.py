from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os

# --- Importar módulos ---
from gramatica import Gramatica
from primeros_siguientes import CalculadorPrimerosSiguientes
from analizador_ll1 import AnalizadorLL1
from analizador_slr1 import AnalizadorSLR1

# -------------------------------------------------
# Configuración de la app
# -------------------------------------------------
app = FastAPI(title="API de Análisis de Gramáticas", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Servir el frontend directamente desde FastAPI
# -------------------------------------------------
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

@app.get("/")
def root():
    return FileResponse(os.path.join(frontend_path, "index.html"))


# -------------------------------------------------
# Función auxiliar: parser de texto
# -------------------------------------------------
def parsear_gramatica(texto: str):
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    producciones = {}
    for linea in lineas:
        if "->" not in linea:
            raise ValueError(f"Línea inválida: {linea}")
        lhs, rhs = linea.split("->", 1)
        lhs = lhs.strip()
        rhs = rhs.replace(" ", "")
        alternativas = [alt.strip() for alt in rhs.split("|")]
        producciones[lhs] = alternativas
    return producciones


# -------------------------------------------------
# Endpoint principal
# -------------------------------------------------
@app.post("/api/analizar")
async def analizar_gramatica(request: Request):
    data = await request.json()
    texto_gramatica = data.get("gramatica", "")
    cadena = data.get("cadena", "")

    if not texto_gramatica:
        return JSONResponse(status_code=400, content={"error": "No se recibió ninguna gramática."})

    try:
        dict_prod = parsear_gramatica(texto_gramatica)
        g = Gramatica(dict_prod)

        # Calcular conjuntos
        calc = CalculadorPrimerosSiguientes(g)
        primeros = calc.calcular_primeros()
        siguientes = calc.calcular_siguientes()

        # Crear analizadores
        ll1 = AnalizadorLL1(g, primeros, siguientes)
        slr1 = AnalizadorSLR1(g, primeros, siguientes)

        # Resultado base
        resultado = {
            "gramatica": str(g),
            "primeros": {k: sorted(list(v)) for k, v in primeros.items()},
            "siguientes": {k: sorted(list(v)) for k, v in siguientes.items()},
            "es_ll1": ll1.es_ll1(),
            "es_slr1": slr1.es_slr1(),
            "tabla_ll1": ll1.tabla_analisis if ll1.es_ll1() else {},
            "tabla_slr_action": slr1.tabla_action if hasattr(slr1, 'tabla_action') else {},
            "tabla_slr_goto": slr1.tabla_goto if hasattr(slr1, 'tabla_goto') else {},
            "cadena": cadena,
            "aceptada_ll1": None,
            "aceptada_slr1": None,
        }

        # Probar la cadena (si hay)
        if cadena:
            entrada = cadena if cadena.endswith('$') else cadena + '$'
            if ll1.es_ll1():
                resultado["aceptada_ll1"] = ll1.analizar(entrada)
            if slr1.es_slr1():
                resultado["aceptada_slr1"] = slr1.analizar(entrada)

        # IMPORTANTE: incluir también las tablas para simulación
        if hasattr(slr1, "tabla_action") and hasattr(slr1, "tabla_goto"):
            resultado["tabla_slr_action"] = slr1.tabla_action
            resultado["tabla_slr_goto"] = slr1.tabla_goto

        return JSONResponse(content=resultado)

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.get("/api/test")
def test():
    return {"mensaje": " API funcionando correctamente"}


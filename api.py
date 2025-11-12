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
# Función auxiliar: parser de texto con validaciones
# -------------------------------------------------
def parsear_gramatica(texto: str):
    """
    Parser de gramáticas con validaciones y soporte para símbolos multicaracter.
    - Verifica formato correcto en cada línea.
    - Separa tokens por espacios.
    - 'e' representa epsilon (cadena vacía).
    """
    if not texto.strip():
        raise ValueError("La gramática está vacía. Por favor, ingresa al menos una producción.")

    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    producciones = {}

    for i, linea in enumerate(lineas, start=1):
        # Validar estructura
        if "->" not in linea:
            raise ValueError(f"Error en línea {i}: falta '->' en '{linea}'")

        lhs, rhs = linea.split("->", 1)
        lhs = lhs.strip()
        rhs = rhs.strip()

        if not lhs:
            raise ValueError(f"Error en línea {i}: no se especificó el lado izquierdo (LHS).")

        if not rhs:
            raise ValueError(f"Error en línea {i}: no hay producciones después de '->'.")

        # Validar que el LHS no contenga espacios (solo un símbolo no terminal)
        if " " in lhs:
            raise ValueError(f"Error en línea {i}: el no terminal '{lhs}' no debe contener espacios.")

        # Validar caracteres permitidos (letras, dígitos, guión bajo, comillas, paréntesis, etc.)
        import re
        if not re.match(r"^[A-Za-z0-9_'\(\)\+\*\-]*$", lhs):
            raise ValueError(f"Error en línea {i}: el no terminal '{lhs}' contiene caracteres inválidos.")

        alternativas = [alt.strip() for alt in rhs.split("|") if alt.strip()]
        if not alternativas:
            raise ValueError(f"Error en línea {i}: no se encontró ninguna alternativa después de '->'.")

        # MERGE de alternativas
        if lhs not in producciones:
            producciones[lhs] = []

        for alt in alternativas:
            if alt == "e":
                producciones[lhs].append([])  # epsilon
            else:
                # Si el usuario separa por espacios, respétalo (soporta tokens multicaracter).
                # Si NO hay espacios, divide por caracteres (fallback) para casos como "aA".
                if " " in alt.strip():
                    tokens = alt.split()
                else:
                    import re
                    TOKEN_RE = re.compile(r"id|[A-Za-z]+'|[A-Za-z]+|[()+*]|\$|ε|e")
                    tokens = TOKEN_RE.findall(alt.strip())
                if any(tok == "epsilon" for tok in tokens):
                    raise ValueError(f"Error en línea {i}: usa 'e' en lugar de 'epsilon'.")
                producciones[lhs].append(tokens)

    # Validar duplicados
    for lhs, rhs_list in producciones.items():
        seen = set()
        for rhs in rhs_list:
            rhs_str = " ".join(rhs)
            if rhs_str in seen:
                raise ValueError(f"Producción duplicada detectada: {lhs} -> {rhs_str}")
            seen.add(rhs_str)

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

        # Filtrar solo no terminales para FIRST/FOLLOW
        primeros_filtrados = {nt: sorted(list(v - {'$'}))
                              for nt, v in primeros.items()
                              if nt in g.no_terminales}
        siguientes_filtrados = {nt: sorted(list(v - {'e', 'ε'}))
                                for nt, v in siguientes.items()
                                if nt in g.no_terminales}

        # Resultado base
        resultado = {
            "gramatica": str(g),
            "no_terminales": sorted(list(g.no_terminales)),
            "terminales": sorted(list(g.terminales - {'$', 'e', 'ε'})),
            "primeros": primeros_filtrados,
            "siguientes": siguientes_filtrados,
            "es_ll1": ll1.es_ll1(),
            "es_slr1": slr1.es_slr1(),
            "tabla_ll1": ll1.tabla_analisis if ll1.es_ll1() else {},
            "tabla_slr_action": slr1.tabla_action if hasattr(slr1, 'tabla_action') else {},
            "tabla_slr_goto": slr1.tabla_goto if hasattr(slr1, 'tabla_goto') else {},
            "cadena": cadena,
            "aceptada_ll1": None,
            "aceptada_slr1": None,
        }

        # Agregar mensajes de conflicto (si existen)
        if hasattr(ll1, "error_conflicto") and ll1.error_conflicto:
            resultado["detalle_ll1"] = ll1.error_conflicto
        else:
            resultado["detalle_ll1"] = None

        if hasattr(slr1, "error_conflicto") and slr1.error_conflicto:
            resultado["detalle_slr1"] = slr1.error_conflicto
        else:
            resultado["detalle_slr1"] = None

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
        mensaje = str(e)
        # Si el mensaje ya empieza con "Error", no duplicar el prefijo
        if mensaje.lower().startswith("error"):
            mensaje = mensaje[6:].strip()  # elimina "Error" o "error" al inicio
        return JSONResponse(status_code=400, content={"error": f"Error {mensaje}"})


@app.get("/api/test")
def test():
    return {"mensaje": " API funcionando correctamente"}

"""
Módulo de gramática para los analizadores.
Clase Gramatica para representar gramáticas libres de contexto.
"""

class Gramatica:
    """
    Representación de una gramática libre de contexto.
    """
    def __init__(self, producciones):
        """
        producciones: dict mapping no-terminal -> list de RHS (strings)
        """
        self.producciones = producciones
        # El primer no-terminal es el símbolo inicial
        self.simbolo_inicio = next(iter(producciones)) if producciones else None
        # Conjunto de no-terminales
        self.no_terminales = set(producciones.keys())
        # Validación de consistencia básica
        if not self.no_terminales:
            raise ValueError("La gramática no contiene ningún no terminal válido.")
        # Asegurar que el símbolo inicial tenga producciones
        if self.simbolo_inicio not in producciones:
            raise ValueError(f"El símbolo inicial '{self.simbolo_inicio}' no tiene producciones definidas.")
        
        # Detectar terminales (compatible con tokens multicaracter)
        self.terminales = set()
        for rhs_lista in producciones.values():
            for rhs in rhs_lista:
                # rhs puede ser lista (nuevo formato) o string (caso antiguo)
                tokens = rhs if isinstance(rhs, list) else list(rhs)
                for simbolo in tokens:
                    if simbolo == 'e':
                        continue
                    if simbolo not in self.no_terminales:
                        self.terminales.add(simbolo)

        # Agregar marcador de fin
        self.terminales.add('$')

        # Normalizar producciones
        self._normalizar_producciones()

    def _normalizar_producciones(self):
        """
        Convierte RHS en tuplas y maneja epsilon ('e') como tupla vacía.
        Compatible con producciones que ya vienen como listas de tokens.
        """
        normalizadas = {}
        if not self.producciones:
            raise ValueError("No hay producciones válidas para normalizar.")
        for lhs, rhs_lista in self.producciones.items():
            normalizadas[lhs] = []
            for rhs in rhs_lista:
                if isinstance(rhs, list):
                    # caso nuevo: lista de tokens ['id'] o ['(', 'E', ')']
                    normalizadas[lhs].append(tuple(rhs))
                elif rhs == 'e':
                    normalizadas[lhs].append(())
                else:
                    normalizadas[lhs].append(tuple(rhs))
        self.producciones = normalizadas

    def obtener_producciones(self, no_terminal):
        return self.producciones.get(no_terminal, [])

    def obtener_todas_producciones(self):
        todas = []
        for lhs, rhs_lista in self.producciones.items():
            for rhs in rhs_lista:
                todas.append((lhs, rhs))
        return todas

    def tiene_produccion_epsilon(self, no_terminal):
        for rhs in self.producciones.get(no_terminal, []):
            if len(rhs) == 0:
                return True
        return False

    def __str__(self):
        lineas = []
        for lhs, rhs_lista in self.producciones.items():
            partes_rhs = []
            for rhs in rhs_lista:
                if len(rhs) == 0:
                    partes_rhs.append('e')
                else:
                    partes_rhs.append(' '.join(rhs))
            lineas.append(f"{lhs} -> {' | '.join(partes_rhs)}")
        return '\n'.join(lineas)
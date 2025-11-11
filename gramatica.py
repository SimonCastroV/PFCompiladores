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
        # Detectar terminales
        self.terminales = set()
        for rhs_lista in producciones.values():
            for rhs in rhs_lista:
                for simbolo in rhs:
                    # En esta convención, los no terminales son mayúsculas; 'e' = epsilon
                    if simbolo != 'e' and not simbolo[0].isupper():
                        self.terminales.add(simbolo)
        # Agregar marcador de fin
        self.terminales.add('$')
        # Normalizar producciones
        self._normalizar_producciones()

    def _normalizar_producciones(self):
        """
        Convierte RHS en tuplas y maneja epsilon ('e') como tupla vacía.
        """
        normalizadas = {}
        for lhs, rhs_lista in self.producciones.items():
            normalizadas[lhs] = []
            for rhs in rhs_lista:
                if rhs == 'e':
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
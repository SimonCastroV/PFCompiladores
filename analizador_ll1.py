"""
Analizador LL(1) (top-down).
Construye la tabla LL(1) y permite analizar cadenas.
"""

class AnalizadorLL1:
    def __init__(self, gramatica, primeros, siguientes):
        self.gramatica = gramatica
        self.primeros = primeros
        self.siguientes = siguientes
        self.tabla_analisis = None
        try:
            self.tabla_analisis = self._construir_tabla()
        except ValueError:
            # No es LL(1)
            pass

    def _construir_tabla(self):
        tabla = {}
        for nt in self.gramatica.no_terminales:
            tabla[nt] = {}
        for lhs in self.gramatica.no_terminales:
            for rhs in self.gramatica.obtener_producciones(lhs):
                primeros_rhs = self._primeros_de_secuencia(rhs)
                for term in primeros_rhs:
                    if term != 'e':
                        if term in tabla[lhs]:
                            raise ValueError(f"Conflicto LL(1) en [{lhs}, {term}]")
                        else:
                            tabla[lhs][term] = rhs
                if 'e' in primeros_rhs:
                    for term in self.siguientes[lhs]:
                        if term in tabla[lhs]:
                            raise ValueError(f"Conflicto LL(1) en [{lhs}, {term}]")
                        else:
                            tabla[lhs][term] = rhs
        return tabla

    def _primeros_de_secuencia(self, secuencia):
        if not secuencia:
            return {'e'}
        resultado = set()
        todos_nulos = True
        for simbolo in secuencia:
            if simbolo in self.gramatica.terminales:
                resultado.add(simbolo)
                todos_nulos = False
                break
            for s in self.primeros[simbolo] - {'e'}:
                resultado.add(s)
            if 'e' not in self.primeros[simbolo]:
                todos_nulos = False
                break
        if todos_nulos:
            resultado.add('e')
        return resultado

    def es_ll1(self):
        return self.tabla_analisis is not None

    def analizar(self, cadena_entrada):
        if not self.es_ll1():
            return False
        tokens = list(cadena_entrada)
        if not tokens or tokens[-1] != '$':
            tokens.append('$')
        pila = ['$', self.gramatica.simbolo_inicio]
        i = 0
        while pila:
            cima = pila.pop()
            simbolo = tokens[i] if i < len(tokens) else '$'
            if cima in self.gramatica.terminales or cima == '$':
                if cima == simbolo:
                    i += 1
                else:
                    return False
            else:
                if cima in self.tabla_analisis and simbolo in self.tabla_analisis[cima]:
                    produccion = self.tabla_analisis[cima][simbolo]
                    if produccion:
                        for s in reversed(produccion):
                            pila.append(s)
                else:
                    return False
        return (i == len(tokens)) or (i == len(tokens) - 1 and tokens[i] == '$')
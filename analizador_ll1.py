"""
Analizador LL(1) (predictivo descendente).
Construye la tabla LL(1) y permite analizar cadenas.
Compatible con la clase Gramatica y el cálculo de Primeros/Siguientes.
"""

class AnalizadorLL1:
    def __init__(self, gramatica, primeros, siguientes):
        self.gramatica = gramatica
        self.primeros = primeros
        self.siguientes = siguientes
        self.tabla_analisis = None
        self.error_conflicto = None

        try:
            self.tabla_analisis = self._construir_tabla()
        except ValueError as e:
            self.error_conflicto = str(e)
            self.tabla_analisis = None

    # ==========================================================
    #               CONSTRUCCIÓN DE TABLA LL(1)
    # ==========================================================
    def _construir_tabla(self):
        tabla = {nt: {} for nt in self.gramatica.no_terminales}

        for lhs in self.gramatica.no_terminales:
            for rhs in self.gramatica.obtener_producciones(lhs):
                primeros_rhs = self._primeros_de_secuencia(rhs)

                # Caso normal: símbolos terminales en FIRST(rhs)
                for term in primeros_rhs - {'e'}:
                    if term in tabla[lhs]:
                        raise ValueError(
                            f"Conflicto LL(1): múltiple predicción para [{lhs}, {term}]"
                        )
                    tabla[lhs][term] = rhs

                # Caso especial: producción puede derivar epsilon
                if 'e' in primeros_rhs:
                    for term in self.siguientes[lhs]:
                        if term in tabla[lhs]:
                            raise ValueError(
                                f"Conflicto LL(1): múltiple predicción para [{lhs}, {term}]"
                            )
                        tabla[lhs][term] = rhs
        return tabla

    # ==========================================================
    #                 FUNCIONES AUXILIARES
    # ==========================================================
    def _primeros_de_secuencia(self, secuencia):
        """
        Calcula FIRST de una secuencia (rhs) completa.
        """
        if not secuencia:
            return {'e'}

        resultado = set()
        for simbolo in secuencia:
            resultado |= (self.primeros[simbolo] - {'e'})
            if 'e' not in self.primeros[simbolo]:
                break
        else:
            resultado.add('e')
        return resultado

    def es_ll1(self):
        return self.tabla_analisis is not None

    # ==========================================================
    #                     ANÁLISIS LL(1)
    # ==========================================================
    def analizar(self, cadena_entrada):
        """
        Analiza una cadena usando la tabla LL(1).
        Retorna True si la cadena pertenece al lenguaje.
        """
        if not self.es_ll1():
            return False

        import re
        SYM_RE = re.compile(r"id|[A-Za-z]+'|[A-Za-z]+|[()+*]|\$")
        tokens = SYM_RE.findall(cadena_entrada.replace(" ", ""))

        if not tokens or tokens[-1] != '$':
            tokens.append('$')

        pila = ['$', self.gramatica.simbolo_inicio]
        i = 0

        while pila:
            cima = pila.pop()
            simbolo = tokens[i] if i < len(tokens) else '$'

            if cima == simbolo == '$':
                return True

            if cima in self.gramatica.terminales:
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
        return False
    
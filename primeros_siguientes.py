"""
Cálculo de Primeros y Siguientes para gramáticas.
"""

class CalculadorPrimerosSiguientes:
    """
    Calculador de conjuntos Primero y Siguiente.
    """
    def __init__(self, gramatica):
        self.gramatica = gramatica
        self.nullable = {nt: self.gramatica.tiene_produccion_epsilon(nt) for nt in self.gramatica.no_terminales}

    def calcular_primeros(self):
        primeros = {}
        # Inicializar para terminales
        for t in self.gramatica.terminales:
            primeros[t] = {t}
        # Inicializar para no-terminales
        for nt in self.gramatica.no_terminales:
            primeros[nt] = set()
            if self.gramatica.tiene_produccion_epsilon(nt):
                primeros[nt].add('e')
        cambiado = True
        while cambiado:
            cambiado = False
            for nt in self.gramatica.no_terminales:
                for rhs in self.gramatica.obtener_producciones(nt):
                    if not rhs:
                        if 'e' not in primeros[nt]:
                            primeros[nt].add('e')
                            cambiado = True
                        continue
                    # Si el primer símbolo es terminal
                    if rhs[0] in self.gramatica.terminales:
                        if rhs[0] not in primeros[nt]:
                            primeros[nt].add(rhs[0])
                            cambiado = True
                        continue
                    # Si son no-terminales
                    todo_epsilon = True
                    for simbolo in rhs:
                        for s in primeros[simbolo] - {'e'}:
                            if s not in primeros[nt]:
                                primeros[nt].add(s)
                                cambiado = True
                        if 'e' not in primeros[simbolo]:
                            todo_epsilon = False
                            break
                    if todo_epsilon and 'e' not in primeros[nt]:
                        primeros[nt].add('e')
                        cambiado = True
        return primeros

    def calcular_siguientes(self):
        siguientes = {nt: set() for nt in self.gramatica.no_terminales}
        siguientes[self.gramatica.simbolo_inicio].add('$')
        primeros = self.calcular_primeros()
        cambiado = True
        while cambiado:
            cambiado = False
            for nt in self.gramatica.no_terminales:
                for rhs in self.gramatica.obtener_producciones(nt):
                    if not rhs:
                        continue
                    for i in range(len(rhs)):
                        simbolo = rhs[i]
                        if simbolo not in self.gramatica.no_terminales:
                            continue
                        if i == len(rhs) - 1:
                            for s in siguientes[nt]:
                                if s not in siguientes[simbolo]:
                                    siguientes[simbolo].add(s)
                                    cambiado = True
                        else:
                            primero_beta = self._primeros_de_secuencia(rhs[i+1:], primeros)
                            for s in primero_beta - {'e'}:
                                if s not in siguientes[simbolo]:
                                    siguientes[simbolo].add(s)
                                    cambiado = True
                            if 'e' in primero_beta:
                                for s in siguientes[nt]:
                                    if s not in siguientes[simbolo]:
                                        siguientes[simbolo].add(s)
                                        cambiado = True
        return siguientes

    def _primeros_de_secuencia(self, secuencia, primeros):
        if not secuencia:
            return {'e'}
        resultado = set()
        todo_epsilon = True
        for simbolo in secuencia:
            resultado.update(primeros[simbolo] - {'e'})
            if 'e' not in primeros[simbolo]:
                todo_epsilon = False
                break
        if todo_epsilon:
            resultado.add('e')
        return resultado

    def _puede_derive_epsilon(self, simbolo, primeros):
        return simbolo in self.gramatica.no_terminales and 'e' in primeros[simbolo]

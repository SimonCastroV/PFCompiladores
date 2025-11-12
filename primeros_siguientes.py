"""
Cálculo de conjuntos PRIMEROS y SIGUIENTES para gramáticas libres de contexto.
Compatible con la clase Gramatica.
"""

class CalculadorPrimerosSiguientes:
    def __init__(self, gramatica):
        self.gramatica = gramatica
        # Marcar no terminales que pueden derivar epsilon
        self.nullable = {
            nt: self.gramatica.tiene_produccion_epsilon(nt)
            for nt in self.gramatica.no_terminales
        }

    # ==========================================================
    #                     CÁLCULO DE PRIMEROS
    # ==========================================================
    def calcular_primeros(self):
        primeros = {}

        # 1️⃣ Inicializar terminales
        for t in self.gramatica.terminales:
            primeros[t] = {t}

        # 2️⃣ Inicializar no terminales
        for nt in self.gramatica.no_terminales:
            primeros[nt] = set()
            if self.gramatica.tiene_produccion_epsilon(nt):
                primeros[nt].add('e')

        # 3️⃣ Iterar hasta alcanzar punto fijo
        cambiado = True
        while cambiado:
            cambiado = False
            for nt in self.gramatica.no_terminales:
                for rhs in self.gramatica.obtener_producciones(nt):
                    # Producción vacía (epsilon)
                    if not rhs:
                        if 'e' not in primeros[nt]:
                            primeros[nt].add('e')
                            cambiado = True
                        continue

                    # Caso: primer símbolo terminal
                    if rhs[0] in self.gramatica.terminales:
                        if rhs[0] not in primeros[nt]:
                            primeros[nt].add(rhs[0])
                            cambiado = True
                        continue

                    # Caso: secuencia de no terminales / mezcla
                    todo_epsilon = True
                    for simbolo in rhs:
                        for s in primeros.get(simbolo, set()) - {'e'}:
                            if s not in primeros[nt]:
                                primeros[nt].add(s)
                                cambiado = True
                        if 'e' not in primeros.get(simbolo, set()):
                            todo_epsilon = False
                            break
                    if todo_epsilon and 'e' not in primeros[nt]:
                        primeros[nt].add('e')
                        cambiado = True
        return primeros

    # ==========================================================
    #                     CÁLCULO DE SIGUIENTES
    # ==========================================================
    def calcular_siguientes(self):
        siguientes = {nt: set() for nt in self.gramatica.no_terminales}
        siguientes[self.gramatica.simbolo_inicio].add('$')

        primeros = self.calcular_primeros()

        cambiado = True
        while cambiado:
            cambiado = False
            for nt in self.gramatica.no_terminales:
                for rhs in self.gramatica.obtener_producciones(nt):
                    for i, simbolo in enumerate(rhs):
                        if simbolo not in self.gramatica.no_terminales:
                            continue

                        # Caso 1: simbolo al final → FOLLOW(nt)
                        if i == len(rhs) - 1:
                            for s in siguientes[nt]:
                                if s not in siguientes[simbolo]:
                                    siguientes[simbolo].add(s)
                                    cambiado = True
                        else:
                            # Caso 2: hay símbolos después → FIRST(beta)
                            beta = rhs[i + 1:]
                            primero_beta = self._primeros_de_secuencia(beta, primeros)

                            for s in primero_beta - {'e'}:
                                if s not in siguientes[simbolo]:
                                    siguientes[simbolo].add(s)
                                    cambiado = True

                            # Caso 3: si beta ⇒ ε → FOLLOW(nt)
                            if 'e' in primero_beta or 'ε' in primero_beta:
                                for s in siguientes[nt]:
                                    if s not in siguientes[simbolo] and s not in {'e', 'ε'}:
                                        siguientes[simbolo].add(s)
                                        cambiado = True
        return siguientes

    # ==========================================================
    #                    FUNCIONES AUXILIARES
    # ==========================================================
    def _primeros_de_secuencia(self, secuencia, primeros):
        """
        Devuelve FIRST de una secuencia (lista de símbolos).
        """
        if not secuencia:
            return {'e'}

        resultado = set()
        for simbolo in secuencia:
            resultado.update(primeros.get(simbolo, set()) - {'e'})
            if 'e' not in primeros.get(simbolo, set()):
                break
        else:
            resultado.add('e')
        return resultado

    def _puede_derive_epsilon(self, simbolo, primeros):
        return (
            simbolo in self.gramatica.no_terminales
            and 'e' in primeros.get(simbolo, set())
        )

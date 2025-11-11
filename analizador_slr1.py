"""
Analizador SLR(1) (bottom-up).
Construye colección canónica, tablas ACTION/GOTO y analiza cadenas.
"""

class AnalizadorSLR1:
    def __init__(self, gramatica, primeros, siguientes):
        self.gramatica = gramatica
        self.primeros = primeros
        self.siguientes = siguientes
        self.coleccion_canonica = None
        self.tabla_action = None
        self.tabla_goto = None
        try:
            self.coleccion_canonica = self._construir_coleccion_canonica()
            self.tabla_action, self.tabla_goto = self._construir_tablas()
        except ValueError:
            pass

    def _cierre_items(self, items):
        cierre = set(items)
        cambiado = True
        while cambiado:
            cambiado = False
            nuevos = set()
            for lhs, rhs, pos in cierre:
                if pos >= len(rhs):
                    continue
                simbolo_sig = rhs[pos]
                if simbolo_sig in self.gramatica.no_terminales:
                    for rhs_nt in self.gramatica.obtener_producciones(simbolo_sig):
                        nuevo_item = (simbolo_sig, rhs_nt, 0)
                        if nuevo_item not in cierre:
                            nuevos.add(nuevo_item)
                            cambiado = True
            cierre.update(nuevos)
        return cierre

    def _ir_a(self, items, simbolo):
        conjunto = set()
        for lhs, rhs, pos in items:
            if pos >= len(rhs):
                continue
            if rhs[pos] == simbolo:
                conjunto.add((lhs, rhs, pos + 1))
        return self._cierre_items(conjunto)

    def _construir_coleccion_canonica(self):
        aumentado_inicio = "S'"
        rhs_inicio = (self.gramatica.simbolo_inicio,)
        item_inicial = (aumentado_inicio, rhs_inicio, 0)
        conjunto_inicial = self._cierre_items({item_inicial})
        coleccion = [conjunto_inicial]
        pendientes = [0]
        while pendientes:
            idx = pendientes.pop(0)
            estado = coleccion[idx]
            todos_simbolos = list(self.gramatica.terminales) + list(self.gramatica.no_terminales)
            for simbolo in todos_simbolos:
                goto_set = self._ir_a(estado, simbolo)
                if goto_set:
                    for j, est_existente in enumerate(coleccion):
                        if goto_set == est_existente:
                            break
                    else:
                        coleccion.append(goto_set)
                        pendientes.append(len(coleccion) - 1)
        return coleccion

    def _construir_tablas(self):
        if not self.coleccion_canonica:
            raise ValueError("No se puede construir sin colección canónica")
        action = [{} for _ in range(len(self.coleccion_canonica))]
        goto = [{} for _ in range(len(self.coleccion_canonica))]
        transiciones = {}
        for i, estado in enumerate(self.coleccion_canonica):
            for simbolo in list(self.gramatica.terminales) + list(self.gramatica.no_terminales):
                goto_set = self._ir_a(estado, simbolo)
                if goto_set:
                    for j, est in enumerate(self.coleccion_canonica):
                        if goto_set == est:
                            transiciones[(i, simbolo)] = j
                            break
        for i, estado in enumerate(self.coleccion_canonica):
            for lhs, rhs, pos in estado:
                if pos < len(rhs):
                    sig = rhs[pos]
                    if sig in self.gramatica.terminales:
                        if (i, sig) in transiciones:
                            j = transiciones[(i, sig)]
                            if sig in action[i]:
                                raise ValueError(f"Conflicto SLR(1) en estado {i}, símbolo '{sig}'")
                            action[i][sig] = ('shift', j)
                else:
                    if lhs == "S'" and pos == 1 and rhs[0] == self.gramatica.simbolo_inicio:
                        if '$' in action[i]:
                            raise ValueError(f"Conflicto SLR(1) en estado {i}, símbolo '$'")
                        action[i]['$'] = ('accept', None)
                    else:
                        for term in self.siguientes[lhs]:
                            if term in action[i]:
                                raise ValueError(f"Conflicto SLR(1) en estado {i}, símbolo '{term}'")
                            prod_idx = -1
                            for idx, (p_lhs, p_rhs) in enumerate(self.gramatica.obtener_todas_producciones()):
                                if p_lhs == lhs and p_rhs == rhs:
                                    prod_idx = idx
                                    break
                            action[i][term] = ('reduce', (lhs, rhs))
            for nt in self.gramatica.no_terminales:
                if (i, nt) in transiciones:
                    goto[i][nt] = transiciones[(i, nt)]
        return action, goto

    def es_slr1(self):
        return self.tabla_action is not None and self.tabla_goto is not None

    def analizar(self, cadena_entrada):
        if not self.es_slr1():
            return False
        tokens = list(cadena_entrada)
        if not tokens or tokens[-1] != '$':
            tokens.append('$')
        pila = [0]
        i = 0
        while True:
            estado = pila[-1]
            simbolo = tokens[i] if i < len(tokens) else None
            if self.tabla_action is None or estado not in range(len(self.tabla_action)) or simbolo not in self.tabla_action[estado]:
                return False
            accion, objetivo = self.tabla_action[estado][simbolo]
            if accion == 'shift':
                pila.append(simbolo)
                pila.append(objetivo)
                i += 1
            elif accion == 'reduce':
                lhs, rhs = objetivo
                if rhs:
                    for _ in range(len(rhs) * 2):
                        pila.pop()
                estado_actual = pila[-1]
                pila.append(lhs)
                if self.tabla_goto is None or estado_actual not in range(len(self.tabla_goto)) or lhs not in self.tabla_goto[estado_actual]:
                    return False
                goto_estado = self.tabla_goto[estado_actual][lhs]
                pila.append(goto_estado)
            elif accion == 'accept':
                return True
            else:
                return False
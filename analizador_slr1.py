"""
Analizador SLR(1) (bottom-up).
Construye la colección canónica de ítems LR(0),
las tablas ACTION y GOTO, y permite analizar cadenas.
"""

class AnalizadorSLR1:
    def __init__(self, gramatica, primeros, siguientes):
        self.gramatica = gramatica
        self.primeros = primeros
        self.siguientes = siguientes
        self.coleccion_canonica = None
        self.tabla_action = None
        self.tabla_goto = None
        self.error_conflicto = None

        try:
            self.coleccion_canonica = self._construir_coleccion_canonica()
            self.tabla_action, self.tabla_goto = self._construir_tablas()
        except ValueError as e:
            self.error_conflicto = str(e)
            self.coleccion_canonica = None
            self.tabla_action = None
            self.tabla_goto = None

    # ==========================================================
    #              CIERRE E IR_A DE ÍTEMS LR(0)
    # ==========================================================
    def _cierre_items(self, items):
        cierre = set(items)
        cambiado = True
        while cambiado:
            cambiado = False
            nuevos = set()
            for lhs, rhs, pos in cierre:
                if pos < len(rhs):
                    simbolo = rhs[pos]
                    if simbolo in self.gramatica.no_terminales:
                        for prod in self.gramatica.obtener_producciones(simbolo):
                            item = (simbolo, prod, 0)
                            if item not in cierre:
                                nuevos.add(item)
                                cambiado = True
            cierre |= nuevos
        return cierre

    def _ir_a(self, items, simbolo):
        avanzados = {
            (lhs, rhs, pos + 1)
            for (lhs, rhs, pos) in items
            if pos < len(rhs) and rhs[pos] == simbolo
        }
        return self._cierre_items(avanzados)

    # ==========================================================
    #             COLECCIÓN CANÓNICA LR(0)
    # ==========================================================
    def _construir_coleccion_canonica(self):
        aumentado_inicio = "S'"
        rhs_inicio = (self.gramatica.simbolo_inicio,)
        inicial = self._cierre_items({(aumentado_inicio, rhs_inicio, 0)})

        coleccion = [inicial]
        pendientes = [0]

        while pendientes:
            i = pendientes.pop(0)
            estado = coleccion[i]

            # ✅ Corrección: unir conjuntos de forma segura
            todos_simbolos = (self.gramatica.terminales - {'$'}) | set(self.gramatica.no_terminales)

            for simbolo in todos_simbolos:
                goto_set = self._ir_a(estado, simbolo)
                if goto_set and goto_set not in coleccion:
                    coleccion.append(goto_set)
                    pendientes.append(len(coleccion) - 1)
        return coleccion

    # ==========================================================
    #              TABLAS ACTION / GOTO
    # ==========================================================
    def _construir_tablas(self):
        if not self.coleccion_canonica:
            raise ValueError("No se puede construir sin colección canónica")

        n = len(self.coleccion_canonica)
        action = [{} for _ in range(n)]
        goto = [{} for _ in range(n)]

        transiciones = {}

        # Construir transiciones
        for i, estado in enumerate(self.coleccion_canonica):
            # ✅ Corrección aquí también
            for simbolo in (self.gramatica.terminales - {'$'}) | set(self.gramatica.no_terminales):
                goto_set = self._ir_a(estado, simbolo)
                if goto_set:
                    j = next((idx for idx, s in enumerate(self.coleccion_canonica) if s == goto_set), None)
                    if j is not None:
                        transiciones[(i, simbolo)] = j

        # Construir ACTION y GOTO
        for i, estado in enumerate(self.coleccion_canonica):
            for lhs, rhs, pos in estado:
                # Shift
                if pos < len(rhs):
                    a = rhs[pos]
                    if a in self.gramatica.terminales:
                        if (i, a) in transiciones:
                            j = transiciones[(i, a)]
                            if a in action[i] and action[i][a] != ('shift', j):
                                raise ValueError(f"Conflicto shift/reduce en estado {i}, símbolo {a}")
                            action[i][a] = ('shift', j)

                # Reduce o Aceptar
                else:
                    if lhs == "S'" and rhs == (self.gramatica.simbolo_inicio,):
                        action[i]['$'] = ('accept', None)
                    else:
                        for a in self.siguientes[lhs]:
                            if a not in self.gramatica.terminales and a != '$':
                                continue
                            if a in action[i]:
                                raise ValueError(f"Conflicto reduce/reduce en estado {i} con {a}")
                            action[i][a] = ('reduce', (lhs, rhs))

            # GOTO
            for A in self.gramatica.no_terminales:
                if (i, A) in transiciones:
                    goto[i][A] = transiciones[(i, A)]

        return action, goto

    # ==========================================================
    #                     ANÁLISIS SLR(1)
    # ==========================================================
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
            simbolo = tokens[i]

            if simbolo not in self.tabla_action[estado]:
                return False

            accion, valor = self.tabla_action[estado][simbolo]

            if accion == 'shift':
                pila.append(simbolo)
                pila.append(valor)
                i += 1
            elif accion == 'reduce':
                lhs, rhs = valor
                for _ in range(2 * len(rhs)):
                    pila.pop()
                estado_actual = pila[-1]
                pila.append(lhs)
                pila.append(self.tabla_goto[estado_actual][lhs])
            elif accion == 'accept':
                return True
            else:
                return False

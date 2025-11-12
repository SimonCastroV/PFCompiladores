"""
Analizador SLR(1) con construcción formal de:
- Conjuntos canónicos de ítems LR(0) (CLOSURE / GOTO)
- Tablas ACTION y GOTO
- Bucle de análisis shift-reduce con pila de estados

Compatible con:
 - clase Gramatica (producciones como tuplas, epsilon = tupla vacía)
 - conjuntos FIRST y FOLLOW calculados externamente
"""

from collections import defaultdict, deque

class AnalizadorSLR1:
    def __init__(self, gramatica, primeros, siguientes):
        self.g = gramatica
        self.primeros = primeros
        self.follow = siguientes  # FOLLOW(A) se usa para reducciones
        self.aug_inicio = self._augmentar_inicio(self.g.simbolo_inicio)

        # Estructuras de autómata
        self.items = []            # lista de conjuntos LR(0) (cada uno es frozenset de items)
        self.transitions = {}      # (idx_estado, simbolo) -> idx_estado
        self.tabla_action = {}     # estado -> { terminal : [acciones...] }
        self.tabla_goto = {}       # estado -> { no_terminal : estado }
        self.error_conflicto = None

        # Construcción
        self._construir_automata_lr0()
        self._construir_tablas_slr()

    # ==========================
    #   Representación de ítems
    # ==========================
    # Ítem LR(0): (A, rhs_tuple, dot_pos)
    #   A -> α • β   se representa con dot_pos=len(α)

    def _augmentar_inicio(self, S):
        # S' -> S
        aug = S + "'"
        while aug in self.g.no_terminales:
            aug += "'"
        return aug

    def _items_de(self, no_terminal):
        """ Devuelve lista de (A, rhs) para A=no_terminal """
        return [(no_terminal, rhs) for rhs in self.g.obtener_producciones(no_terminal)]

    def _closure(self, I):
        """
        Cierre LR(0) clásico.
        I: set de ítems (A, rhs, dot)
        """
        cambiando = True
        I = set(I)
        while cambiando:
            cambiando = False
            # Recorremos copia estática para poder añadir
            for (A, rhs, dot) in list(I):
                # ¿Punto antes de un no terminal?
                if dot < len(rhs):
                    X = rhs[dot]
                    if X in self.g.no_terminales:
                        for (B, beta) in self._items_de(X):
                            itm = (B, beta, 0)
                            if itm not in I:
                                I.add(itm)
                                cambiando = True
        return frozenset(I)

    def _goto(self, I, X):
        """
        GOTO(I, X) = CLOSURE({A -> αX•β | A->α•Xβ ∈ I})
        """
        J = set()
        for (A, rhs, dot) in I:
            if dot < len(rhs) and rhs[dot] == X:
                J.add((A, rhs, dot + 1))
        if not J:
            return None
        return self._closure(J)

    def _construir_automata_lr0(self):
        """
        Construye la colección canónica de conjuntos LR(0) y las transiciones.
        """
        # Producción aumentada: S' -> S
        prod_aug = {self.aug_inicio: [(self.g.simbolo_inicio,)]}
        # Integramos temporalmente en una gramatica de lectura
        # (no tocamos self.g.producciones)
        def producciones_de(A):
            if A == self.aug_inicio:
                return [tuple(p) for p in prod_aug[A]]
            return self.g.obtener_producciones(A)

        # I0 = CLOSURE(S' -> • S)
        I0 = self._closure({(self.aug_inicio, (self.g.simbolo_inicio,), 0)})
        self.items = [I0]
        pendientes = deque([0])
        self.transitions = {}

        while pendientes:
            i = pendientes.popleft()
            I = self.items[i]

            # Símbolos candidatos desde I: lo que aparece justo después del punto
            simbolos = set()
            for (A, rhs, dot) in I:
                if dot < len(rhs):
                    simbolos.add(rhs[dot])

            for X in simbolos:
                J = self._goto(I, X)
                if J is None:
                    continue
                # ¿Existe ya?
                if J in self.items:
                    j = self.items.index(J)
                else:
                    self.items.append(J)
                    j = len(self.items) - 1
                    pendientes.append(j)
                self.transitions[(i, X)] = j

        # Inicializar estructuras de tablas
        for i in range(len(self.items)):
            self.tabla_action[i] = defaultdict(list)
            self.tabla_goto[i] = {}

    # ==========================
    #    Construcción SLR(1)
    # ==========================
    def _construir_tablas_slr(self):
        """
        ACTION y GOTO según SLR(1):
        - shift si existe GOTO por un terminal
        - reduce A -> α si el ítem A->α• está en I y, para todo a∈FOLLOW(A), ACTION[i,a] = reduce A->α
        - accept si el ítem S'->S• está en I
        """
        conflictos = []

        # Conjuntos útiles
        terminals = set(self.g.terminales) - {'$'}   # agregaremos $ aparte para accept
        terminals.add('$')  # para accept

        for i, I in enumerate(self.items):
            # 1) shifts por terminales
            # si (i, a) existe transición, ACTION[i,a] = shift j
            for a in terminals:
                if (i, a) in self.transitions:
                    j = self.transitions[(i, a)]
                    self._add_action(i, a, f"shift {j}", conflictos)

            # 2) gotos por no terminales
            for A in self.g.no_terminales.union({self.aug_inicio}):
                if (i, A) in self.transitions:
                    j = self.transitions[(i, A)]
                    if A != self.aug_inicio:  # no mostramos goto de S'
                        self.tabla_goto[i][A] = j

            # 3) reducciones y accept
            for (A, rhs, dot) in I:
                # A -> α •    (punto al final)
                if dot == len(rhs):
                    if A == self.aug_inicio:
                        # S' -> S •  ⇒ accept sobre $
                        self._add_action(i, '$', "accept", conflictos)
                        continue

                    # reduce A -> rhs sobre cada a ∈ FOLLOW(A)
                    rhs_texto = " ".join(rhs) if len(rhs) > 0 else "e"
                    acc = f"reduce {A},{rhs_texto}"
                    for a in self.follow.get(A, set()):
                        self._add_action(i, a, acc, conflictos)

        # Guardar conflictos si hubo
        if conflictos:
            # mensaje compacto (primer conflicto)
            self.error_conflicto = conflictos[0]

        # Eliminar llaves vacías en ACTION
        for i in range(len(self.items)):
            self.tabla_action[i] = dict(self.tabla_action[i])

    def _add_action(self, i, a, accion, conflictos):
        """
        Inserta una acción en ACTION[i][a] detectando conflictos S/R o R/R.
        """
        celdas = self.tabla_action[i][a]
        if celdas and accion not in celdas:
            # Conflicto
            conflictos.append(f"Conflicto SLR(1) en estado {i}, símbolo '{a}': {celdas} vs {accion}")
        if accion not in celdas:
            celdas.append(accion)

    def es_slr1(self):
        # Es SLR(1) si no hubo conflictos
        return self.error_conflicto is None

    # ==========================
    #      Análisis SLR(1)
    # ==========================
    def analizar(self, cadena_entrada):
        """
        Analiza usando las tablas ACTION/GOTO (shift-reduce).
        cadena_entrada: string de símbolos (caracteres), se agrega '$' si falta.
        """
        if not self.es_slr1():
            return False

        # Tokenización simple compatible con tu frontend actual
        tokens = list(cadena_entrada)
        if not tokens or tokens[-1] != '$':
            tokens.append('$')

        # Pila de estados (no mezclamos símbolos aquí; el frontend solo usa tablas)
        pila = [0]
        i = 0

        while True:
            estado = pila[-1]
            a = tokens[i] if i < len(tokens) else '$'

            accion = self.tabla_action.get(estado, {}).get(a, [])
            if not accion:
                return False

            # Preferimos 'accept' > shift > reduce si hubiera más de una (no debería si es SLR(1))
            if "accept" in accion:
                return True

            # Si hay shift y reduce, igual se consideraría conflicto, pero por seguridad:
            if any(x.startswith("shift") for x in accion):
                # Tomar el primero 'shift n'
                act = next(x for x in accion if x.startswith("shift"))
                n = int(act.split()[1])
                pila.append(n)
                i += 1
                continue

            # Si hay reduce
            if any(x.startswith("reduce") for x in accion):
                act = next(x for x in accion if x.startswith("reduce"))
                # reduce A,alpha
                _, resto = act.split(" ", 1)
                A, rhs_txt = resto.split(",", 1)
                rhs = [] if rhs_txt.strip() == "e" else rhs_txt.strip().split()

                # Pop por |rhs|
                k = len(rhs)
                if k > len(pila):
                    return False
                for _ in range(k):
                    pila.pop()

                # Estado t = cima después de pop
                t = pila[-1] if pila else 0
                if A not in self.tabla_goto.get(t, {}):
                    return False
                pila.append(self.tabla_goto[t][A])
                continue

            # Si ninguna de las anteriores aplicó, error
            return False
        
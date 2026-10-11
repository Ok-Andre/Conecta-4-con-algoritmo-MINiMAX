#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Práctica No. 04 - Búsqueda adversaria
Fundamentos de Inteligencia Artificial - ESCOM, IPN

Conecta-4 (tablero de 6 filas x 7 columnas) con el algoritmo MINIMAX y
poda alfa-beta para decidir la jugada de la computadora.

Uso:
    python conecta4.py                 # juego con interfaz gráfica (tkinter)
    python conecta4.py --benchmark     # compara profundidades 1..N (para el video)
    python conecta4.py --benchmark 7   # idem, hasta profundidad 7
    python conecta4.py --match 2 5     # partida IA(prof 2) vs IA(prof 5)

Estructura del archivo
    1. Constantes y representación del tablero
    2. Reglas del juego (movimientos, victoria)
    3. FUNCIÓN DE EVALUACIÓN HEURÍSTICA (nodos hoja)
    4. GENERACIÓN DEL ÁRBOL DE JUEGO + MINIMAX con poda alfa-beta
    5. Interfaz gráfica
    6. Benchmark / partida IA vs IA
"""

import sys
import time

# ---------------------------------------------------------------------------
# 1. CONSTANTES Y REPRESENTACIÓN DEL TABLERO
# ---------------------------------------------------------------------------
# El tablero es una lista de 6 filas; cada fila es una lista de 7 casillas.
# La fila 0 es la SUPERIOR; la fila 5 es la inferior (donde caen las fichas).
ROWS, COLS = 6, 7
EMPTY, HUMAN, AI = 0, 1, 2          # contenido de una casilla / identificador de jugador
INF = float("inf")
WIN_SCORE = 1_000_000               # valor de un nodo terminal ganador

# Orden de exploración de columnas: del centro hacia afuera.
# Explorar primero las mejores jugadas (el centro) hace que la poda
# alfa-beta corte muchas más ramas.
COLUMN_ORDER = [3, 2, 4, 1, 5, 0, 6]

# Las 4 direcciones en las que se puede formar una línea: →, ↓, ↘, ↗
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (-1, 1)]


def new_board():
    """Devuelve un tablero vacío de 6x7."""
    return [[EMPTY] * COLS for _ in range(ROWS)]


def opponent(player):
    return HUMAN if player == AI else AI


# ---------------------------------------------------------------------------
# 2. REGLAS DEL JUEGO
# ---------------------------------------------------------------------------
def valid_moves(board):
    """Columnas jugables (la casilla superior de la columna está libre),
    ordenadas del centro hacia afuera."""
    return [c for c in COLUMN_ORDER if board[0][c] == EMPTY]


def drop_piece(board, col, player):
    """Deja caer una ficha en la columna `col`. Modifica el tablero en sitio
    y devuelve la fila donde cayó (None si la columna está llena)."""
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == EMPTY:
            board[r][col] = player
            return r
    return None


def undo_piece(board, row, col):
    """Deshace una jugada (permite explorar el árbol sin copiar el tablero)."""
    board[row][col] = EMPTY


def winning_line(board, row, col, player):
    """Si la ficha en (row, col) forma 4 o más en línea, devuelve la lista de
    casillas ganadoras; en caso contrario devuelve None.
    Sólo revisa líneas que pasan por la última ficha jugada (más eficiente
    que revisar todo el tablero en cada nodo)."""
    for dr, dc in DIRECTIONS:
        cells = [(row, col)]
        for sign in (1, -1):                       # se extiende en ambos sentidos
            r, c = row + sign * dr, col + sign * dc
            while 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == player:
                cells.append((r, c))
                r, c = r + sign * dr, c + sign * dc
        if len(cells) >= 4:
            return cells
    return None


def is_win(board, row, col, player):
    return winning_line(board, row, col, player) is not None


# ---------------------------------------------------------------------------
# 3. FUNCIÓN DE EVALUACIÓN (HEURÍSTICA PARA LOS NODOS HOJA)
# ---------------------------------------------------------------------------
# Heurística: "análisis de ventanas de 4 casillas" + control del centro.
#
# En Conecta-4 se gana formando una línea de 4, así que se examinan TODAS las
# "ventanas" de 4 casillas consecutivas (horizontales, verticales y diagonales;
# hay 69 en un tablero 6x7). Cada ventana se puntúa según su contenido:
#
#   Ventana (desde el punto de vista de la IA)        Puntos
#   -----------------------------------------------   ------
#   3 fichas de la IA + 1 hueco  (amenaza de ganar)     +50
#   2 fichas de la IA + 2 huecos (potencial)            +10
#   3 fichas del rival + 1 hueco (amenaza rival)        -80   <- se penaliza
#   2 fichas del rival + 2 huecos                       -10      más que lo que
#   ventanas mixtas o vacías                              0      se premia: la
#                                                                defensa es prioritaria
# Además, las fichas en la columna central participan en más líneas posibles,
# por lo que se bonifican (+6 por ficha de la IA en la columna central, y
# se resta lo mismo por las del rival).
#
# Evaluación final = suma(ventanas) + bonus de centro.
# Positivo => favorece a la computadora (MAX); negativo => favorece al humano (MIN).
WINDOW_SCORES = {
    # (fichas propias, fichas rivales) : puntos
    (3, 0): 50,
    (2, 0): 10,
    (0, 3): -80,
    (0, 2): -10,
}
CENTER_BONUS = 6


def all_windows():
    """Genera una vez las coordenadas de las 69 ventanas de 4 casillas."""
    windows = []
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in DIRECTIONS:
                end_r, end_c = r + 3 * dr, c + 3 * dc
                if 0 <= end_r < ROWS and 0 <= end_c < COLS:
                    windows.append([(r + i * dr, c + i * dc) for i in range(4)])
    return windows


WINDOWS = all_windows()


def evaluate(board):
    """Función de evaluación aplicada a los nodos hoja (profundidad límite
    alcanzada). Devuelve un entero: mayor = mejor para la computadora."""
    score = 0

    # (a) Control de la columna central
    center = COLS // 2
    for r in range(ROWS):
        if board[r][center] == AI:
            score += CENTER_BONUS
        elif board[r][center] == HUMAN:
            score -= CENTER_BONUS

    # (b) Puntuación de cada ventana de 4 casillas
    for window in WINDOWS:
        mine = theirs = 0
        for r, c in window:
            v = board[r][c]
            if v == AI:
                mine += 1
            elif v == HUMAN:
                theirs += 1
        # Sólo cuentan ventanas "limpias" (sin fichas de ambos jugadores)
        score += WINDOW_SCORES.get((mine, theirs), 0)
    return score


# ---------------------------------------------------------------------------
# 4. GENERACIÓN DEL ÁRBOL DE JUEGO Y MINIMAX CON PODA ALFA-BETA
# ---------------------------------------------------------------------------
class Stats:
    """Contadores para analizar el desempeño de la búsqueda."""

    def __init__(self):
        self.nodes = 0      # nodos del árbol generados/visitados
        self.leaves = 0     # nodos hoja evaluados con la heurística
        self.prunes = 0     # cortes alfa-beta realizados
        self.time = 0.0     # segundos


def minimax(board, depth, alpha, beta, maximizing, last_move, stats):
    """MINIMAX con poda alfa-beta.

    ÁRBOL DE JUEGO: no se construye explícitamente en memoria; se genera de
    forma implícita por recursión. Cada llamada es un NODO; cada columna
    válida es una RAMA (jugada) hacia un nodo hijo. Para generar un hijo se
    hace `drop_piece` (aplicar jugada), se llama recursivamente y luego
    `undo_piece` (retroceder). Los niveles alternan:
        nivel MAX  -> turno de la computadora (maximiza el valor)
        nivel MIN  -> turno del humano        (minimiza el valor)

    Parámetros
        depth       niveles restantes por expandir (0 => nodo hoja)
        alpha       mejor valor garantizado para MAX en la ruta actual
        beta        mejor valor garantizado para MIN en la ruta actual
        maximizing  True si en este nodo mueve la computadora
        last_move   (fila, col, jugador) de la última jugada, para detectar
                    victoria sin revisar todo el tablero
    """
    stats.nodes += 1

    # --- Nodo terminal: la última jugada ganó la partida --------------------
    if last_move is not None:
        r, c, p = last_move
        if is_win(board, r, c, p):
            # Se suma `depth` para preferir victorias rápidas (y retrasar
            # las derrotas): a más profundidad restante, el triunfo es más cercano.
            return (WIN_SCORE + depth) if p == AI else -(WIN_SCORE + depth)

    moves = valid_moves(board)
    if not moves:                      # --- Nodo terminal: empate (tablero lleno)
        return 0

    # --- Nodo hoja: límite de profundidad => APLICAR FUNCIÓN DE EVALUACIÓN --
    if depth == 0:
        stats.leaves += 1
        return evaluate(board)

    # --- Nodo interno: GENERAR HIJOS (una rama por columna válida) ----------
    if maximizing:                                      # Nivel MAX (computadora)
        value = -INF
        for col in moves:
            row = drop_piece(board, col, AI)            # generar hijo
            child = minimax(board, depth - 1, alpha, beta, False, (row, col, AI), stats)
            undo_piece(board, row, col)                 # regresar al nodo padre
            value = max(value, child)
            alpha = max(alpha, value)
            if alpha >= beta:                           # PODA BETA: MIN nunca permitirá esta rama
                stats.prunes += 1
                break
        return value
    else:                                               # Nivel MIN (humano)
        value = INF
        for col in moves:
            row = drop_piece(board, col, HUMAN)
            child = minimax(board, depth - 1, alpha, beta, True, (row, col, HUMAN), stats)
            undo_piece(board, row, col)
            value = min(value, child)
            beta = min(beta, value)
            if alpha >= beta:                           # PODA ALFA: MAX ya tiene algo mejor
                stats.prunes += 1
                break
        return value


def best_move(board, depth, player=AI):
    """Raíz del árbol (nivel 0, MAX): evalúa cada jugada posible con MINIMAX
    y devuelve (mejor_columna, valor, estadísticas).
    `player` permite que la IA juegue con cualquiera de los dos colores
    (se usa en el modo --match)."""
    global AI, HUMAN
    # Si `player` no es AI, se intercambian los identificadores de rol
    # temporalmente para que minimax/evaluate lo traten como "la computadora".
    swapped = player != AI
    if swapped:
        AI, HUMAN = HUMAN, AI
    try:
        stats = Stats()
        t0 = time.perf_counter()
        best_col, best_val = None, -INF
        alpha, beta = -INF, INF
        for col in valid_moves(board):
            row = drop_piece(board, col, AI)
            val = minimax(board, depth - 1, alpha, beta, False, (row, col, AI), stats)
            undo_piece(board, row, col)
            if val > best_val:                 # estricto: ante empate prefiere el centro
                best_val, best_col = val, col
            alpha = max(alpha, best_val)
        stats.time = time.perf_counter() - t0
        return best_col, best_val, stats
    finally:
        if swapped:
            AI, HUMAN = HUMAN, AI


# ---------------------------------------------------------------------------
# 5. INTERFAZ GRÁFICA (tkinter)
# ---------------------------------------------------------------------------
def run_gui():
    import tkinter as tk
    from tkinter import messagebox

    CELL = 90
    PAD = 10
    COLORS = {EMPTY: "#e6e6ea", HUMAN: "#e53935", AI: "#fdd835"}

    class Connect4App:
        def __init__(self, root):
            self.root = root
            root.title("Conecta-4 · MINIMAX con poda alfa-beta")
            root.resizable(False, False)

            # ---- Panel de control ----
            top = tk.Frame(root, padx=8, pady=6)
            top.pack(fill="x")
            tk.Label(top, text="Profundidad:").pack(side="left")
            self.depth_var = tk.IntVar(value=4)
            tk.Spinbox(top, from_=1, to=9, width=3, textvariable=self.depth_var).pack(side="left", padx=4)
            self.first_var = tk.StringVar(value="Humano")
            tk.Label(top, text="  Inicia:").pack(side="left")
            tk.OptionMenu(top, self.first_var, "Humano", "Computadora").pack(side="left")
            tk.Button(top, text="Nueva partida", command=self.new_game).pack(side="right")

            # ---- Tablero ----
            w = COLS * CELL + 2 * PAD
            h = ROWS * CELL + 2 * PAD
            self.canvas = tk.Canvas(root, width=w, height=h, bg="#1e4fb5", highlightthickness=0)
            self.canvas.pack()
            self.canvas.bind("<Button-1>", self.on_click)

            # ---- Barra de estado y estadísticas ----
            self.status = tk.Label(root, text="", font=("Arial", 12, "bold"), pady=4)
            self.status.pack()
            self.info = tk.Label(root, text="", font=("Consolas", 9), justify="left", pady=2)
            self.info.pack()

            self.new_game()

        # ----- ciclo de la partida -----
        def new_game(self):
            self.board = new_board()
            self.game_over = False
            self.thinking = False
            self.win_cells = []
            self.info.config(text="")
            self.draw()
            if self.first_var.get() == "Computadora":
                self.status.config(text="La computadora piensa…")
                self.thinking = True
                self.root.after(100, self.computer_move)
            else:
                self.status.config(text="Tu turno (rojo): haz clic en una columna")

        def on_click(self, event):
            if self.game_over or self.thinking:
                return
            col = (event.x - PAD) // CELL
            if not 0 <= col < COLS or self.board[0][col] != EMPTY:
                return
            row = drop_piece(self.board, col, HUMAN)
            self.draw()
            if self.check_end(row, col, HUMAN):
                return
            self.thinking = True
            self.status.config(text="La computadora piensa…")
            self.root.after(50, self.computer_move)   # deja que la GUI se redibuje

        def computer_move(self):
            depth = max(1, min(9, self.depth_var.get()))
            col, val, st = best_move(self.board, depth)
            row = drop_piece(self.board, col, AI)
            self.info.config(
                text=f"Última jugada IA: columna {col + 1}  |  profundidad {depth}  |  valor {val}\n"
                     f"Nodos: {st.nodes:,}  Hojas evaluadas: {st.leaves:,}  "
                     f"Podas: {st.prunes:,}  Tiempo: {st.time:.3f} s")
            self.thinking = False
            self.draw()
            if not self.check_end(row, col, AI):
                self.status.config(text="Tu turno (rojo): haz clic en una columna")

        def check_end(self, row, col, player):
            line = winning_line(self.board, row, col, player)
            if line:
                self.win_cells = line
                self.game_over = True
                self.draw()
                msg = "¡Ganaste!" if player == HUMAN else "Gana la computadora"
                self.status.config(text=msg)
                messagebox.showinfo("Fin de la partida", msg)
                return True
            if not valid_moves(self.board):
                self.game_over = True
                self.status.config(text="Empate")
                messagebox.showinfo("Fin de la partida", "Empate")
                return True
            return False

        def draw(self):
            self.canvas.delete("all")
            for r in range(ROWS):
                for c in range(COLS):
                    x0, y0 = PAD + c * CELL + 6, PAD + r * CELL + 6
                    x1, y1 = x0 + CELL - 12, y0 + CELL - 12
                    win = (r, c) in self.win_cells
                    self.canvas.create_oval(
                        x0, y0, x1, y1, fill=COLORS[self.board[r][c]],
                        outline="black" if win else "#16397f", width=5 if win else 2)
            for c in range(COLS):                      # numeración de columnas
                self.canvas.create_text(PAD + c * CELL + CELL // 2, 6, text=str(c + 1),
                                        fill="white", font=("Arial", 8))
            self.root.update_idletasks()

    root = tk.Tk()
    Connect4App(root)
    root.mainloop()


# ---------------------------------------------------------------------------
# 6. BENCHMARK Y PARTIDA IA vs IA (útiles para la demostración del video)
# ---------------------------------------------------------------------------
def print_board(board):
    sym = {EMPTY: ".", HUMAN: "X", AI: "O"}
    for row in board:
        print(" ".join(sym[v] for v in row))
    print("1 2 3 4 5 6 7\n")


def benchmark(max_depth=6):
    """Compara el costo de la búsqueda con distintas profundidades en una
    posición de medio juego."""
    board = new_board()
    for col, player in [(3, HUMAN), (3, AI), (2, HUMAN), (4, AI), (2, HUMAN), (2, AI)]:
        drop_piece(board, col, player)
    print("Posición de prueba:")
    print_board(board)
    print(f"{'Prof.':>5} {'Jugada':>7} {'Valor':>9} {'Nodos':>12} {'Hojas':>12} {'Podas':>10} {'Tiempo(s)':>10}")
    for d in range(1, max_depth + 1):
        col, val, st = best_move(board, d)
        print(f"{d:>5} {col + 1:>7} {val:>9} {st.nodes:>12,} {st.leaves:>12,} {st.prunes:>10,} {st.time:>10.3f}")


def match(depth_a, depth_b):
    """Partida automática: IA con profundidad `depth_a` (juega 'O') contra IA con
    profundidad `depth_b` (juega 'X'). Muestra qué profundidad rinde mejor."""
    board = new_board()
    turn = AI
    depths = {AI: depth_a, HUMAN: depth_b}
    while True:
        col, _, _ = best_move(board, depths[turn], player=turn)
        row = drop_piece(board, col, turn)
        if is_win(board, row, col, turn):
            print_board(board)
            name = "O" if turn == AI else "X"
            print(f"Gana {name} (profundidad {depths[turn]})")
            return
        if not valid_moves(board):
            print_board(board)
            print("Empate")
            return
        turn = opponent(turn)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--benchmark":
        benchmark(int(args[1]) if len(args) > 1 else 6)
    elif args and args[0] == "--match" and len(args) == 3:
        match(int(args[1]), int(args[2]))
    else:
        run_gui()

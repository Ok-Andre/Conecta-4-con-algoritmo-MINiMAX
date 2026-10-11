#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas de desempeño de la Práctica 04 (Conecta-4).

    python benchmark.py poda         # MINIMAX con y sin poda, profundidades 1..N
    python benchmark.py torneo       # todos contra todos entre profundidades
    python benchmark.py heuristica   # heurística de ventanas vs. tabla posicional
    python benchmark.py todo         # las tres pruebas

Todas usan semilla fija (42) para que los resultados sean repetibles.
Los resultados se guardan en results_<prueba>.json.
"""
import json
import random
import sys
import time
from itertools import combinations

import conecta4 as c

SEED = 42


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def posiciones_medio_juego(n=10, plies=9, seed=SEED):
    """Genera n posiciones de medio juego jugando `plies` fichas al azar
    (sin que nadie haya ganado). Con plies impar y empezando HUMAN, le toca mover a la IA."""
    rng = random.Random(seed)
    posiciones = []
    while len(posiciones) < n:
        b = c.new_board()
        turno = c.HUMAN
        ok = True
        for _ in range(plies):
            col = rng.choice(c.valid_moves(b))
            r = c.drop_piece(b, col, turno)
            if c.is_win(b, r, col, turno):
                ok = False
                break
            turno = c.opponent(turno)
        if ok:
            posiciones.append(b)
    return posiciones


def minimax_sin_poda(board, depth, maximizing, last_move, stats):
    """MINIMAX puro (sin alfa-beta): sirve de referencia para medir el ahorro de la poda."""
    stats.nodes += 1
    if last_move is not None:
        r, col, p = last_move
        if c.is_win(board, r, col, p):
            return (c.WIN_SCORE + depth) if p == c.AI else -(c.WIN_SCORE + depth)
    moves = c.valid_moves(board)
    if not moves:
        return 0
    if depth == 0:
        stats.leaves += 1
        return c.evaluate(board)
    player = c.AI if maximizing else c.HUMAN
    vals = []
    for m in moves:
        r = c.drop_piece(board, m, player)
        vals.append(minimax_sin_poda(board, depth - 1, not maximizing, (r, m, player), stats))
        c.undo_piece(board, r, m)
    return max(vals) if maximizing else min(vals)


def valor_raiz_sin_poda(board, depth):
    st = c.Stats()
    t0 = time.perf_counter()
    best = -c.INF
    for m in c.valid_moves(board):
        r = c.drop_piece(board, m, c.AI)
        v = minimax_sin_poda(board, depth - 1, False, (r, m, c.AI), st)
        c.undo_piece(board, r, m)
        best = max(best, v)
    st.time = time.perf_counter() - t0
    return best, st


# ---------------------------------------------------------------------------
# Prueba 1: efecto de la profundidad y de la poda
# ---------------------------------------------------------------------------
def prueba_poda(max_depth=9, max_depth_sin_poda=6):
    pos = posiciones_medio_juego()
    filas = []
    print(f"{'Prof':>4} | {'CON PODA nodos':>15} {'hojas':>10} {'podas':>9} {'t(s)':>7} |"
          f" {'SIN PODA nodos':>15} {'t(s)':>7} | {'reducción':>9} | mismo valor")
    for d in range(1, max_depth + 1):
        n = h = p = 0
        t = 0.0
        n0 = 0
        t0 = 0.0
        iguales = True
        for b in pos:
            col, val, st = c.best_move(b, d)
            n += st.nodes; h += st.leaves; p += st.prunes; t += st.time
            if d <= max_depth_sin_poda:
                v0, st0 = valor_raiz_sin_poda(b, d)
                n0 += st0.nodes; t0 += st0.time
                iguales &= (v0 == val)
        k = len(pos)
        fila = {"depth": d, "nodos": n / k, "hojas": h / k, "podas": p / k, "tiempo": t / k}
        if d <= max_depth_sin_poda:
            fila.update({"nodos_sin": n0 / k, "tiempo_sin": t0 / k,
                         "reduccion": 1 - n / n0, "mismo_valor": iguales})
        filas.append(fila)
        sin = (f"{n0 / k:>15,.0f} {t0 / k:>7.3f} | {100 * (1 - n / n0):>8.1f}% | {iguales}"
               if d <= max_depth_sin_poda else "")
        print(f"{d:>4} | {n / k:>15,.0f} {h / k:>10,.0f} {p / k:>9,.0f} {t / k:>7.3f} | {sin}")
    json.dump(filas, open("results_poda.json", "w"), indent=1)
    return filas


# ---------------------------------------------------------------------------
# Prueba 2: torneo entre profundidades
# ---------------------------------------------------------------------------
def jugar(depth_o, depth_x, rng, eval_o=None, eval_x=None, apertura=2):
    """Juega una partida. 'O' (AI) usa depth_o y eval_o; 'X' (HUMAN) usa depth_x y eval_x.
    Las primeras `apertura` fichas son aleatorias para que las partidas difieran.
    Mueve primero O. Devuelve 'O', 'X' o 'E' (empate) y el número de jugadas."""
    b = c.new_board()
    turno = c.AI
    original_eval = c.evaluate
    plies = 0
    try:
        while True:
            if plies < apertura:
                col = rng.choice(c.valid_moves(b))
            else:
                d = depth_o if turno == c.AI else depth_x
                ev = eval_o if turno == c.AI else eval_x
                c.evaluate = ev or original_eval
                col, _, _ = c.best_move(b, d, player=turno)
            r = c.drop_piece(b, col, turno)
            plies += 1
            if c.is_win(b, r, col, turno):
                return ("O" if turno == c.AI else "X"), plies
            if not c.valid_moves(b):
                return "E", plies
            turno = c.opponent(turno)
    finally:
        c.evaluate = original_eval


def prueba_torneo(depths=(1, 2, 3, 4, 5, 6), partidas=10):
    rng = random.Random(SEED)
    resultados = []
    puntos = {d: 0.0 for d in depths}
    print(f"{'Duelo':>9} | {'gana A':>6} {'gana B':>6} {'empates':>7}")
    for a, b in combinations(depths, 2):
        ga = gb = ge = 0
        for i in range(partidas):
            # se alterna quién empieza (O mueve primero)
            if i % 2 == 0:
                g, _ = jugar(a, b, rng)
                g = {"O": "A", "X": "B", "E": "E"}[g]
            else:
                g, _ = jugar(b, a, rng)
                g = {"O": "B", "X": "A", "E": "E"}[g]
            ga += g == "A"; gb += g == "B"; ge += g == "E"
        puntos[a] += ga + 0.5 * ge
        puntos[b] += gb + 0.5 * ge
        resultados.append({"A": a, "B": b, "gana_A": ga, "gana_B": gb, "empates": ge})
        print(f"{a:>3} vs {b:<3} | {ga:>6} {gb:>6} {ge:>7}")
    print("Puntos totales (victoria=1, empate=0.5):", puntos)
    json.dump({"duelos": resultados, "puntos": puntos, "partidas": partidas},
              open("results_torneo.json", "w"), indent=1)


# ---------------------------------------------------------------------------
# Prueba 3: comparación de heurísticas
# ---------------------------------------------------------------------------
# Heurística alternativa: tabla de valor posicional (cada casilla vale según
# cuántas líneas de 4 pasan por ella). Es una baseline clásica y simple.
TABLA = [[3, 4, 5, 7, 5, 4, 3],
         [4, 6, 8, 10, 8, 6, 4],
         [5, 8, 11, 13, 11, 8, 5],
         [5, 8, 11, 13, 11, 8, 5],
         [4, 6, 8, 10, 8, 6, 4],
         [3, 4, 5, 7, 5, 4, 3]]


def eval_posicional(board):
    s = 0
    for r in range(c.ROWS):
        for col in range(c.COLS):
            v = board[r][col]
            if v == c.AI:
                s += TABLA[r][col]
            elif v == c.HUMAN:
                s -= TABLA[r][col]
    return s


def prueba_heuristica(depths=(2, 4), partidas=20):
    rng = random.Random(SEED)
    ventanas = c.evaluate            # heurística propuesta
    out = []
    print(f"{'Prof':>4} | {'ventanas':>8} {'posicional':>10} {'empates':>7}")
    for d in depths:
        gv = gp = ge = 0
        for i in range(partidas):
            if i % 2 == 0:   # ventanas = O (empieza), posicional = X
                g, _ = jugar(d, d, rng, eval_o=ventanas, eval_x=eval_posicional)
                g = {"O": "V", "X": "P", "E": "E"}[g]
            else:            # posicional = O (empieza), ventanas = X
                g, _ = jugar(d, d, rng, eval_o=eval_posicional, eval_x=ventanas)
                g = {"O": "P", "X": "V", "E": "E"}[g]
            gv += g == "V"; gp += g == "P"; ge += g == "E"
        out.append({"depth": d, "ventanas": gv, "posicional": gp, "empates": ge, "partidas": partidas})
        print(f"{d:>4} | {gv:>8} {gp:>10} {ge:>7}")
    json.dump(out, open("results_heuristica.json", "w"), indent=1)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "todo"
    if what in ("poda", "todo"):
        prueba_poda()
    if what in ("torneo", "todo"):
        prueba_torneo()
    if what in ("heuristica", "todo"):
        prueba_heuristica()

"""
patterns.py — Patrones conocidos para verificar correctitud.

Dependencias: grid.
Lo usan: tests/test_patterns, y opcionalmente la GUI (botón de ejemplos).
"""


def _colocar(grid, r, c, celdas):
    """Pone vivas las celdas (dr, dc) relativas a (r, c). Las que caen fuera se ignoran."""
    h = len(grid)
    w = len(grid[0])
    for dr, dc in celdas:
        if 0 <= r + dr < h and 0 <= c + dc < w:
            grid[r + dr][c + dc] = 1


def place_blinker(grid, r, c):
    """Coloca un blinker (oscilador de periodo 2: 3 celdas en línea) con esquina en (r, c).

    Prueba esperada: tras 1 generación queda rotado; tras 2 es igual al original.
    """
    _colocar(grid, r, c, [(0, 0), (0, 1), (0, 2)])


def place_glider(grid, r, c):
    """Coloca un glider con esquina en (r, c).

    Prueba esperada: tras 4 generaciones es el MISMO patrón desplazado (+1, +1).
    Usar una matriz con espacio de sobra; con frontera muerta choca y se deforma,
    con frontera muerta choca contra la pared (útil para probar los bordes).
    """
    _colocar(grid, r, c, [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)])


def place_block(grid, r, c):
    """Coloca un bloque 2x2 (vida estable). Prueba esperada: nunca cambia."""
    _colocar(grid, r, c, [(0, 0), (0, 1), (1, 0), (1, 1)])

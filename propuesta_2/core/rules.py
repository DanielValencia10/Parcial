"""
rules.py — La lógica del juego, escrita UNA SOLA VEZ.

Dependencias: grid, config.
Lo usan: v1_sequential, v2_threads, v3_processes, v4_hybrid, v5_mpi.

POR QUÉ UNA SOLA VEZ: si cada versión copia la regla, un cambio en una la deja
distinta de las demás y la comparación de rendimiento deja de ser justa. Aquí solo
cambia QUIÉN recorre QUÉ filas.

Reglas del enunciado:
  - Viva con < 2 vecinos vivos        -> muere
  - Viva con 2 o 3 vecinos vivos      -> sobrevive
  - Viva con > 3 vecinos vivos        -> muere
  - Muerta con exactamente 3 vecinos  -> nace

ANTI-RACE-CONDITION [VISTO EN CLASE: Sesión Concurrencia, "vector independiente"]:
  compute_rows LEE de src y ESCRIBE solo en dst (doble búfer). Cada trabajador
  escribe filas distintas de dst => no hay dos escritores sobre la misma celda
  => no hace falta Lock. "La mejor sincronización es la que no necesitas."
  Con UNA sola matriz, una celda ya actualizada contaminaría a su vecina y el
  resultado dependería del orden de ejecución.

DOS NIVELES (decisión de diseño):
  - next_cell_state / count_neighbors: versión CELDA A CELDA, clara, con la regla tal
    cual la escribe el enunciado. Es la REFERENCIA: los tests comparan el kernel
    rápido contra ella.
  - compute_rows: versión RÁPIDA por filas, la que usan TODAS las versiones.
    Primero suma, columna a columna, las tres filas vecinas; luego suma tres columnas
    contiguas. El bucle interno no usa módulos ni índices (solo zip).

FRONTERA "MUERTA" (config.FRONTERA): todo lo que queda FUERA de la matriz cuenta como
celda muerta (0). Una celda del borde simplemente tiene menos vecinos.
  - Vertical: la fila de arriba de la fila 0 y la de abajo de la última son filas de ceros.
    Si compute_rows se llama con una banda + filas fantasma y el rango (1, len - 1), nunca
    sale de la banda: los fantasmas ya traen los vecinos (o ceros en los extremos de la
    matriz). Por eso el MISMO kernel sirve para V1, V2, V3 y V5.
  - Horizontal: a cada fila se le pega un 0 a la izquierda y otro a la derecha (relleno de
    1 columna), lo que también resuelve las 4 esquinas.
"""

_CERO = b"\x00"


def next_cell_state(current, neighbors):
    """Aplica las 4 reglas a una celda.

    Entradas: current (0/1), neighbors (0..8).
    Salida: nuevo estado (0/1).
    """
    if current == 1:
        if neighbors < 2:
            return 0          # soledad
        if neighbors > 3:
            return 0          # sobrepoblación
        return 1              # 2 o 3 vecinos: sobrevive
    return 1 if neighbors == 3 else 0     # muerta: nace con exactamente 3


def count_neighbors(src, r, c):
    """Cuenta los vecinos vivos (8 direcciones) de la celda (r, c).

    Frontera muerta (config.FRONTERA): lo que cae fuera de la matriz no se cuenta.
    Versión de REFERENCIA (lenta, índice a índice): se usa en los tests.
    """
    h = len(src)
    w = len(src[0])
    total = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue                      # la celda no es su propio vecino
            rr = r + dr
            cc = c + dc
            if 0 <= rr < h and 0 <= cc < w:   # fuera de la matriz = muerta (no suma)
                total += src[rr][cc]
    return total


def compute_rows(src, dst, r_start, r_end):
    """Calcula las filas [r_start, r_end) de la siguiente generación.

    Entradas: src (generación actual, solo lectura), dst (siguiente, escritura),
              r_start y r_end (rango de filas; r_end excluido).
    Salida: ninguna; modifica solo dst[r_start:r_end].
    Uso:
      - V1: una llamada con (0, h).
      - V2: cada hilo con SU banda.
      - V3/V5: el worker con su banda local (incluye filas fantasma) y rango (1, len-1).
    """
    h = len(src)
    ceros = bytes(len(src[0]))                # fila de ceros para los bordes superior/inferior
    for r in range(r_start, r_end):
        arriba = src[r - 1] if r > 0 else ceros
        centro = src[r]
        abajo = src[r + 1] if r + 1 < h else ceros
        # relleno de 1 columna muerta por lado (incluye las esquinas)
        arriba = _CERO + arriba + _CERO
        centro = _CERO + centro + _CERO
        abajo = _CERO + abajo + _CERO
        # suma vertical: vecinos de arriba + centro + abajo, columna a columna
        col = [x + y + z for x, y, z in zip(arriba, centro, abajo)]
        # s = suma de la ventana 3x3 (incluye a la propia celda).
        #   s == 3                 -> nace (muerta con 3) o sobrevive (viva con 2 + ella)
        #   s == 4 y la celda viva -> sobrevive (3 vecinos + ella)
        dst[r][:] = bytes([
            1 if (s := c0 + c1 + c2) == 3 or (s == 4 and viva) else 0
            for c0, c1, c2, viva in zip(col, col[1:], col[2:], centro[1:])
        ])

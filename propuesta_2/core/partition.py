"""
partition.py — Reparto de filas entre trabajadores y filas fantasma.

Dependencias: grid, config.
Lo usan: v2_threads, v3_processes, v4_hybrid, tests/test_partition.

[VISTO EN CLASE: Sesión de Técnicas de descomposición, Taller 2 — descomposición
por dominio: dividir los datos en partes, una por trabajador.]

POR QUÉ FILAS (y no columnas ni bloques 2D):
  - Frontera por banda = 2*W celdas (igual a columnas en matriz cuadrada, pero...)
  - Las filas son memoria contigua => mejor localidad de caché.
  - Bloques 2D reducen el perímetro solo con MUCHOS trabajadores y obligan a
    manejar 8 vecinos + esquinas entre bloques. Con <= 8 trabajadores no compensa.
"""


def row_ranges(h, p):
    """Reparte h filas entre p trabajadores, con balance de carga.

    Entradas: h (filas), p (trabajadores).
    Salida: lista de p tuplas (r_start, r_end), r_end excluido, contiguas y sin
            huecos ni solapes, que cubren exactamente [0, h).
    Regla del residuo: base = h // p, extra = h % p; las primeras `extra` bandas
    reciben UNA fila más. Ej.: 1000 filas / 7 => 6 bandas de 143 y 1 de 142.
    Caso borde: si p > h, limitar p a h (no dejar trabajadores sin filas).
    """
    p = max(1, min(p, h))              # nunca más trabajadores que filas
    base = h // p
    extra = h % p                      # las primeras `extra` bandas llevan una fila más
    rangos = []
    inicio = 0
    for i in range(p):
        tam = base + (1 if i < extra else 0)
        rangos.append((inicio, inicio + tam))
        inicio += tam
    return rangos


def with_ghost_rows(grid, r_start, r_end):
    """Construye la banda de un trabajador más una fila vecina arriba y otra abajo.

    Entradas: grid (matriz completa), r_start/r_end (rango de la banda).
    Salida: (h_banda + 2) filas: [fila_de_arriba] + banda + [fila_de_abajo].
    Frontera muerta: la fila de arriba de la PRIMERA banda y la de abajo de la ÚLTIMA son
    filas de ceros (fuera de la matriz no hay nada vivo). Las demás son filas reales vecinas.
    Se COPIA el dato: es justo el costo de comunicación de V3.
    """
    h = len(grid)
    ancho = len(grid[0])
    arriba = grid[r_start - 1] if r_start > 0 else bytearray(ancho)   # antes de la fila 0: ceros
    abajo = grid[r_end] if r_end < h else bytearray(ancho)            # después de la última: ceros
    banda = [bytearray(f) for f in grid[r_start:r_end]]
    return [bytearray(arriba)] + banda + [bytearray(abajo)]


def strip_ghost_rows(band_with_ghosts):
    """Quita las filas fantasma y devuelve solo las filas propias de la banda."""
    return band_with_ghosts[1:-1]

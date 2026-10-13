"""
test_partition.py — Verifica el reparto de filas (core.partition).

Ejecutar desde la raíz:  python -m tests.test_partition

CASOS (para varias combinaciones de h y p):
  - Los rangos son contiguos, sin huecos ni solapes, y cubren exactamente [0, h).
  - La diferencia de tamaño entre la banda más grande y la más pequeña es <= 1.
  - 1000 filas / 7 trabajadores => seis bandas de 143 y una de 142.
  - p = 1 => una sola banda con todas las filas.
  - p > h => no quedan trabajadores con 0 filas (se limita p).
  - with_ghost_rows con frontera muerta: la fila de arriba de la primera banda y la de
    abajo de la última son filas de CEROS; las demás son las filas reales vecinas.
"""

import sys

from core import grid, partition


def _verificar_rangos(h, p):
    rangos = partition.row_ranges(h, p)
    esperado_p = min(p, h)
    assert len(rangos) == esperado_p, f"h={h} p={p}: {len(rangos)} bandas, se esperaban {esperado_p}"
    assert rangos[0][0] == 0 and rangos[-1][1] == h, f"h={h} p={p}: no cubre [0, h)"
    for (a1, b1), (a2, b2) in zip(rangos, rangos[1:]):
        assert b1 == a2, f"h={h} p={p}: hueco o solape entre {(a1, b1)} y {(a2, b2)}"
    tamanos = [b - a for a, b in rangos]
    assert min(tamanos) >= 1, f"h={h} p={p}: hay una banda vacía"
    assert max(tamanos) - min(tamanos) <= 1, f"h={h} p={p}: desbalance {tamanos}"
    return rangos


def main():
    fallos = 0

    def caso(nombre, funcion):
        nonlocal fallos
        try:
            funcion()
            print(f"OK     {nombre}")
        except AssertionError as exc:
            fallos += 1
            print(f"FALLO  {nombre}: {exc}")

    def barrido():
        for h in (1, 2, 3, 7, 8, 100, 101, 999, 1000):
            for p in (1, 2, 3, 4, 7, 8, 16, 2000):
                _verificar_rangos(h, p)

    def mil_entre_siete():
        tamanos = [b - a for a, b in _verificar_rangos(1000, 7)]
        assert tamanos == [143] * 6 + [142], tamanos

    def un_trabajador():
        assert _verificar_rangos(50, 1) == [(0, 50)]

    def mas_trabajadores_que_filas():
        assert len(_verificar_rangos(3, 8)) == 3

    def fantasmas():
        g = grid.new_grid(12, 5)
        grid.randomize(g, 3, 0.5)
        rangos = partition.row_ranges(12, 3)
        primera = partition.with_ghost_rows(g, *rangos[0])
        ultima = partition.with_ghost_rows(g, *rangos[-1])
        media = partition.with_ghost_rows(g, *rangos[1])
        assert len(primera) == (rangos[0][1] - rangos[0][0]) + 2
        assert primera[0] == bytearray(5), "arriba de la 1ª banda debe ser una fila de ceros (borde muerto)"
        assert ultima[-1] == bytearray(5), "abajo de la última banda debe ser una fila de ceros (borde muerto)"
        assert primera[-1] == g[rangos[0][1]], "abajo de la 1ª banda debe ser la fila real siguiente"
        assert media[0] == g[rangos[1][0] - 1] and media[-1] == g[rangos[1][1]]
        assert partition.strip_ghost_rows(media) == g[rangos[1][0]:rangos[1][1]]
        # es una COPIA: modificarla no toca la matriz original
        media[1][0] ^= 1
        assert media[1] != g[rangos[1][0]]

    caso("rangos contiguos, balanceados y completos (h x p)", barrido)
    caso("1000 filas / 7 trabajadores = 6 x 143 + 1 x 142", mil_entre_siete)
    caso("p = 1 -> una banda con todo", un_trabajador)
    caso("p > h -> se limita p (sin bandas vacías)", mas_trabajadores_que_filas)
    caso("filas fantasma (ceros en los extremos) y copia", fantasmas)

    print("\nTODO OK" if fallos == 0 else f"\n{fallos} caso(s) con FALLO")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()

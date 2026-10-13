"""
test_patterns.py — Verifica el comportamiento con patrones conocidos, en TODAS las versiones.

Ejecutar desde la raíz:  python -m tests.test_patterns
V5 (MPI) exige mpiexec:  mpiexec -n 1 python -m tests.test_patterns --versiones 5
Opciones: --versiones 2,3  para acotar.

CASOS:
  - BLINKER: tras 1 generación está rotado (horizontal <-> vertical); tras 2 es igual
    al original.
  - GLIDER : tras 4 generaciones es el mismo patrón desplazado (+1, +1), en el interior y
    cruzando la frontera ENTRE DOS BANDAS de trabajadores.
  - BLOCK  : nunca cambia (también en una esquina: con borde muerto sigue estable).
  - BORDE  : con frontera muerta, un glider que choca contra la esquina y un blinker pegado
    al borde se comparan generación a generación con el ORÁCULO (regla celda a celda).
  - Cada patrón se coloca en la frontera entre bandas: es el caso que expone un error de
    filas fantasma o de sincronización.
"""

import sys

from core import grid, partition, patterns
from core.v1_sequential import SequentialEngine
from tests import comun

FILAS, COLUMNAS = 32, 32
TRABAJADORES = [1, 2, 4, 8]


def _fila_frontera(workers):
    """Primera fila de la 2ª banda (la frontera entre bandas). Con 1 trabajador, la mitad."""
    rangos = partition.row_ranges(FILAS, workers)
    return rangos[1][0] if len(rangos) > 1 else FILAS // 2


def _correr(version_cls_o_version, workers, inicial, paradas):
    """Avanza un motor desde `inicial` y devuelve {generación: snapshot}. None si no hay motor."""
    if version_cls_o_version == 1:
        motor = SequentialEngine(inicial, workers)
    else:
        motor = comun.crear_motor(version_cls_o_version, inicial, workers)
        if motor is None:
            return None
    resultados = {}
    with motor:
        hechas = 0
        for parada in paradas:
            motor.run(parada - hechas)
            hechas = parada
            resultados[parada] = motor.snapshot()
    return resultados


def test_blinker(version_cls, workers):
    """Verifica el periodo 2 del blinker (sobre la frontera entre bandas)."""
    r = _fila_frontera(workers)
    g = grid.new_grid(FILAS, COLUMNAS)
    patterns.place_blinker(g, r, 10)                    # horizontal en la fila r
    rotado = grid.new_grid(FILAS, COLUMNAS)
    for dr in (-1, 0, 1):                               # vertical: filas r-1, r, r+1 en la columna 11
        rotado[(r + dr) % FILAS][11] = 1
    res = _correr(version_cls, workers, g, [1, 2])
    if res is None:
        return None
    return grid.equals(res[1], rotado) and grid.equals(res[2], g)


def test_glider(version_cls, workers):
    """Verifica el desplazamiento del glider tras 4 y 8 generaciones, cruzando la frontera entre bandas."""
    r, c = _fila_frontera(workers) - 2, 5          # el glider ocupa las filas r..r+2: cruza la frontera
    g = grid.new_grid(FILAS, COLUMNAS)
    patterns.place_glider(g, r, c)
    esperado = grid.new_grid(FILAS, COLUMNAS)
    patterns.place_glider(esperado, r + 1, c + 1)
    esperado8 = grid.new_grid(FILAS, COLUMNAS)
    patterns.place_glider(esperado8, r + 2, c + 2)
    res = _correr(version_cls, workers, g, [4, 8])
    if res is None:
        return None
    return grid.equals(res[4], esperado) and grid.equals(res[8], esperado8)


def test_block(version_cls, workers):
    """Verifica que el bloque no cambia: sobre la frontera entre bandas y en dos esquinas."""
    g = grid.new_grid(FILAS, COLUMNAS)
    patterns.place_block(g, _fila_frontera(workers) - 1, 20)
    patterns.place_block(g, 0, 0)                                # esquina superior izquierda
    patterns.place_block(g, FILAS - 2, COLUMNAS - 2)             # esquina inferior derecha
    res = _correr(version_cls, workers, g, [1, 7])
    if res is None:
        return None
    return grid.equals(res[1], g) and grid.equals(res[7], g)


def test_borde(version_cls, workers):
    """Con borde muerto: glider contra la esquina y blinker pegado al borde, contra el oráculo."""
    GENERACIONES = 12
    g = grid.new_grid(FILAS, COLUMNAS)
    patterns.place_glider(g, FILAS - 6, COLUMNAS - 6)            # va hacia la esquina inferior derecha
    patterns.place_blinker(g, 0, 8)                              # horizontal pegado al borde superior
    patterns.place_blinker(g, _fila_frontera(workers), 0)        # pegado al borde izquierdo y en la frontera entre bandas
    esperado = comun.simular_referencia(g, GENERACIONES)
    res = _correr(version_cls, workers, g, list(range(1, GENERACIONES + 1)))
    if res is None:
        return None
    return all(grid.equals(res[n], esperado[n]) for n in range(1, GENERACIONES + 1))


def main():
    fallos = 0
    saltadas = set()
    pruebas = [("blinker", test_blinker), ("glider", test_glider), ("block", test_block),
               ("borde", test_borde)]
    for version in [1] + comun.versiones_a_probar():
        if version in saltadas:
            continue
        for nombre, prueba in pruebas:
            for p in TRABAJADORES:
                try:
                    ok = prueba(version, p)
                except Exception as exc:                      # noqa: BLE001
                    print(f"FALLO  V{version} {nombre} p={p}: excepción {exc!r}")
                    fallos += 1
                    continue
                if ok is None:
                    saltadas.add(version)
                    break
                if not ok:
                    fallos += 1
                print(f"{'OK    ' if ok else 'FALLO '} V{version} {nombre:<7} p={p}")
            if version in saltadas:
                break
    if saltadas:
        print(f"NOTA: versiones SALTADAS (no verificadas): {sorted(saltadas)}")
    print("\nTODO OK" if fallos == 0 else f"\n{fallos} caso(s) con FALLO")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()

"""
verify_correctness.py — Cada versión paralela debe dar EXACTAMENTE lo mismo que V1.

Ejecutar desde la raíz ANTES de medir rendimiento:  python -m tests.verify_correctness
V5 (MPI) exige mpiexec:  mpiexec -n 1 python -m tests.verify_correctness --versiones 5
Opciones: --versiones 2,3  para acotar.
Script simple con `assert` (sin frameworks): suficiente y dentro de lo visto en clase.

CASOS:
  0. El kernel rápido (rules.compute_rows) contra la regla celda a celda (count_neighbors
     + next_cell_state): garantiza que V1, la referencia, ya es correcta.
  1. Para V2, V3, V4, V5, trabajadores en {1, 2, 3, 4, 7, 8}:
       - mismo grid aleatorio (config.SEMILLA), N generaciones;
       - comparar con la salida de V1 usando grid.equals() y grid.signature().
  2. Tamaños variados, INCLUYENDO filas no divisibles entre los trabajadores
     (1000 filas y 7 trabajadores) y tamaños pequeños (p > h).
  3. Varias generaciones (1, 2, 10, 50): un error en el intercambio de búferes o
     en las filas fantasma aparece después de más de una generación.
  4. Cerrar siempre cada Engine (close()) aunque falle un caso.

SALIDA: línea "OK"/"FALLO" por caso y código de salida distinto de 0 si algo falla.
Windows: bajo `if __name__ == "__main__":` por V3 y V5 (spawn).
"""

import sys

import config
from core import grid, rules
from core.v1_sequential import SequentialEngine
from tests import comun

TAMANOS = [(30, 40), (1000, 16), (5, 9), (3, 3)]       # (filas, columnas)
TRABAJADORES = [1, 2, 3, 4, 7, 8]
CHECKPOINTS = [1, 2, 10, 50]                           # generaciones en las que se compara


def check_kernel_contra_referencia():
    """El kernel por filas == regla celda a celda, en un tablero con bordes y esquinas."""
    g = grid.new_grid(17, 13)
    grid.randomize(g, config.SEMILLA, config.DENSIDAD)
    with SequentialEngine(g) as v1:
        v1.run(1)
        resultado = v1.snapshot()
    for r in range(17):
        for c in range(13):
            esperado = rules.next_cell_state(g[r][c], rules.count_neighbors(g, r, c))
            assert resultado[r][c] == esperado, f"kernel != referencia en ({r},{c})"
    return True


def check_version_against_v1(version, size, workers, generations=None):
    """Compara una versión contra V1 para una configuración. Devuelve True si coinciden.

    Devuelve None si la versión no está disponible (se salta). `generations` puede ser un
    entero o None (= todos los CHECKPOINTS; se compara en cada uno con UN solo motor).
    """
    h, w = size
    g = grid.new_grid(h, w)
    grid.randomize(g, config.SEMILLA, config.DENSIDAD)
    paradas = CHECKPOINTS if generations is None else [generations]

    motor = comun.crear_motor(version, g, workers)
    if motor is None:
        return None
    with SequentialEngine(g) as v1, motor:
        hechas = 0
        for parada in paradas:
            v1.run(parada - hechas)
            motor.run(parada - hechas)
            hechas = parada
            a, b = v1.snapshot(), motor.snapshot()
            if not grid.equals(a, b) or grid.signature(a) != grid.signature(b):
                print(f"FALLO  V{version} {h}x{w} p={workers} en la generación {parada}")
                return False
    return True


def main():
    fallos = 0
    saltados = set()

    try:
        check_kernel_contra_referencia()
        print("OK     kernel rápido == regla celda a celda")
    except AssertionError as exc:
        fallos += 1
        print(f"FALLO  {exc}")

    for version in comun.versiones_a_probar():
        correctos = 0
        total = 0
        for size in TAMANOS:
            for p in TRABAJADORES:
                try:
                    resultado = check_version_against_v1(version, size, p)
                except Exception as exc:                      # noqa: BLE001
                    print(f"FALLO  V{version} {size} p={p}: excepción {exc!r}")
                    resultado = False
                if resultado is None:
                    saltados.add(version)
                    break
                total += 1
                correctos += 1 if resultado else 0
            if version in saltados:
                break
        if version not in saltados:
            fallos += total - correctos
            estado = "OK    " if correctos == total else "FALLO "
            print(f"{estado} V{version}: {correctos}/{total} configuraciones iguales a V1 "
                  f"(tamaños {TAMANOS}, p {TRABAJADORES}, generaciones {CHECKPOINTS})")

    if saltados:
        print(f"NOTA: versiones SALTADAS (no verificadas): {sorted(saltados)}")
    print("\nTODO OK" if fallos == 0 else f"\n{fallos} configuración(es) con FALLO")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()

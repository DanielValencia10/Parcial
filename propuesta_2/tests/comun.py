"""
comun.py — Utilidades compartidas por los tests (no es un test).

Dependencias: core.registry.
Lo usan: verify_correctness, test_patterns.

Decide qué versiones probar y crea los motores. Si una versión no está disponible
(p. ej. V5 sin mpiexec) se SALTA con un aviso claro: no se cuenta como OK ni como fallo.
"""

import sys

from core import grid as grid_mod
from core import rules
from core.registry import EngineUnavailable, load_engine_class

TODAS = [2, 3, 4, 5]          # versiones paralelas (V1 es la referencia)
_avisadas = set()


def versiones_a_probar():
    """Versiones paralelas a probar. Se puede acotar por línea de comandos:  --versiones 2,3"""
    if "--versiones" in sys.argv:
        return [int(v) for v in sys.argv[sys.argv.index("--versiones") + 1].split(",") if int(v) != 1]
    return TODAS


def simular_referencia(inicial, generaciones):
    """ORÁCULO independiente: aplica la regla celda a celda (lenta) `generaciones` veces.

    Usa rules.count_neighbors + rules.next_cell_state, no el kernel rápido. Sirve para
    comprobar casos de borde (glider contra la pared, esquinas) sin calcular a mano el resultado.
    Devuelve {generación: matriz} para cada generación 0..generaciones.
    """
    actual = grid_mod.copy(inicial)
    h, w = len(actual), len(actual[0])
    historia = {0: grid_mod.copy(actual)}
    for g in range(1, generaciones + 1):
        siguiente = grid_mod.new_grid(h, w)
        for r in range(h):
            for c in range(w):
                siguiente[r][c] = rules.next_cell_state(actual[r][c], rules.count_neighbors(actual, r, c))
        actual = siguiente
        historia[g] = grid_mod.copy(actual)
    return historia


def crear_motor(version, grid, workers):
    """Crea el motor de `version`; devuelve None (con aviso una sola vez) si no se puede."""
    try:
        return load_engine_class(version)(grid, workers)
    except EngineUnavailable as exc:
        if version not in _avisadas:
            _avisadas.add(version)
            print(f"SALTADO  V{version}: {exc}")
        return None

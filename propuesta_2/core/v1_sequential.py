"""
v1_sequential.py — V1: versión secuencial en Python puro. BASE DE COMPARACIÓN.

Dependencias: engine_base, grid, rules.

Esquema:
    actual    = copia del estado inicial
    siguiente = matriz vacía del mismo tamaño
    repetir n veces:
        rules.compute_rows(actual, siguiente, 0, h)
        intercambiar las REFERENCIAS actual <-> siguiente (no copiar celdas)

Rendimiento esperado: tiempo proporcional a H * W * G.

TRAMPA SERIAL [VISTO EN CLASE: Sesión Paralelismo]: el bucle de generaciones NO
se puede paralelizar (la generación t+1 depende de la t). Los bucles internos sí.

REGLA DE ORO: el speedup de TODAS las versiones se calcula contra ESTA versión,
no contra "V2 o V3 con 1 trabajador" (esas ya pagan overhead de hilos/procesos).
"""

from core import grid, rules
from core.engine_base import Engine


class SequentialEngine(Engine):
    name = "v1"

    def __init__(self, initial_grid, workers=1):
        # `workers` se ignora: V1 es secuencial. Se acepta para respetar el contrato.
        self.actual = grid.copy(initial_grid)
        self.siguiente = grid.new_grid(len(initial_grid), len(initial_grid[0]))

    def run(self, generations):
        h = len(self.actual)
        for _ in range(generations):
            rules.compute_rows(self.actual, self.siguiente, 0, h)
            self.actual, self.siguiente = self.siguiente, self.actual   # swap de referencias

    def step(self):
        self.run(1)

    def snapshot(self):
        return grid.copy(self.actual)

    def close(self):
        pass        # V1 no tiene hilos ni procesos que liberar

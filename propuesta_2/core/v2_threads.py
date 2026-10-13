"""
v2_threads.py — V2: paralela con `threading`, bandas de filas y Barrier.
Es lo que el enunciado llama "Threads".

Dependencias: engine_base, grid, rules, partition.
Herramientas [VISTO EN CLASE: Taller 3 / Sesión Concurrencia]: Thread, Barrier.
Concepto [VISTO EN CLASE: Sesión VII, Taller 4]: SMP simulado con hilos sobre bloques.

ESQUEMA POR GENERACIÓN:
    cada hilo: compute_rows(actual, siguiente, mi_inicio, mi_fin)
    ── BARRERA ──  (todos terminaron de ESCRIBIR 'siguiente')
    la ACCIÓN de la barrera (se ejecuta UNA vez por ciclo) intercambia actual <-> siguiente
    → todos ven el swap antes de empezar la siguiente generación

ESTRUCTURA SUGERIDA de run(n) con hilos PERSISTENTES:
    barrera de inicio (n_hilos + 1 partes: incluye al hilo que llama) libera a los hilos
    → cada hilo hace n generaciones con UNA barrera por generación (con acción de swap)
    → barrera final avisa al llamador de que terminó
    La GUI llama run(1).

POR QUÉ NO HAY LOCK EN EL CÓMPUTO: lectura de 'actual' (compartida, solo lectura) y
escritura en filas DISJUNTAS de 'siguiente'. Un Lock aquí sería overhead sin beneficio.
Dónde SÍ haría falta: un contador compartido (mejor: parciales por hilo y sumar al final).

RENDIMIENTO ESPERADO: speedup ≈ 1 o menor. Con kernel en Python puro, el GIL permite
ejecutar un solo hilo de Python a la vez; más hilos solo añaden contención y costo de
barreras. ES UN RESULTADO VÁLIDO y parte central del análisis del informe.

RIESGOS:
  - Barrier con número de partes incorrecto => cuelgue (deadlock).
  - Un hilo que falla con excepción deja a los demás bloqueados en la barrera:
    usar timeout y manejar BrokenBarrierError.
  - No crear/destruir hilos por generación.
"""

import threading

from core import grid, partition, rules
from core.engine_base import Engine

# Tiempo máximo que un hilo espera a los demás en la barrera de generación. Si un hilo
# falla, los demás no se quedan colgados para siempre: la barrera se rompe y se reporta.
TIMEOUT_BARRERA = 120


class ThreadedEngine(Engine):
    name = "v2"

    def __init__(self, initial_grid, workers=1):
        self.h = len(initial_grid)
        self.rangos = partition.row_ranges(self.h, workers)   # p efectivo <= filas
        self.p = len(self.rangos)

        self._preparar_estado(initial_grid)       # crea self.actual y self.siguiente

        self._n = 0                 # generaciones que pide el run() en curso
        self._cerrado = False
        self._error = None          # primera excepción ocurrida en un hilo

        # Barrera de INICIO y de FIN: p hilos + el hilo que llama a run() => p + 1 partes.
        # Si el número de partes está mal, run() se cuelga (deadlock).
        self._inicio = threading.Barrier(self.p + 1)
        self._fin = threading.Barrier(self.p + 1)
        # Barrera por GENERACIÓN: solo los p hilos. Su ACCIÓN se ejecuta UNA vez por ciclo,
        # cuando todos terminaron de escribir 'siguiente' y antes de liberar a nadie.
        self._gen = threading.Barrier(self.p, action=self._intercambiar,
                                      timeout=TIMEOUT_BARRERA)

        # Hilos PERSISTENTES: se crean una vez aquí, no por generación.
        self._hilos = [threading.Thread(target=self._trabajar, args=(i,), daemon=True)
                       for i in range(self.p)]
        for hilo in self._hilos:
            hilo.start()

    # --- ganchos que V4 (HybridEngine) reemplaza --------------------------------
    def _preparar_estado(self, initial_grid):
        self.actual = grid.copy(initial_grid)
        self.siguiente = grid.new_grid(len(initial_grid), len(initial_grid[0]))

    def _calcular(self, r_start, r_end):
        """Lo que hace UN hilo en UNA generación: leer actual, escribir su banda de siguiente."""
        rules.compute_rows(self.actual, self.siguiente, r_start, r_end)

    def _exportar(self):
        return grid.copy(self.actual)

    # --- sincronización ----------------------------------------------------------
    def _intercambiar(self):
        """Acción de la barrera: la corre UN solo hilo; los demás están esperando."""
        self.actual, self.siguiente = self.siguiente, self.actual

    def _trabajar(self, i):
        r_start, r_end = self.rangos[i]
        while True:
            self._inicio.wait()                   # espera a que run() lo ponga a trabajar
            if self._cerrado:
                return
            try:
                for _ in range(self._n):
                    self._calcular(r_start, r_end)   # lectura de actual, escritura en MIS filas
                    self._gen.wait()                 # todos escribieron => se hace el swap
            except threading.BrokenBarrierError:
                pass                                 # otro hilo falló; el error real ya se guardó
            except Exception as exc:                 # noqa: BLE001 - se re-lanza en run()
                if self._error is None:
                    self._error = exc
                self._gen.abort()                    # libera a los demás en vez de dejarlos colgados
            self._fin.wait()                         # avisa al llamador de que terminó

    # --- contrato de Engine -------------------------------------------------------
    def run(self, generations):
        if self._cerrado:
            raise RuntimeError("El motor ya fue cerrado")
        if generations <= 0:
            return
        self._n = generations
        self._inicio.wait()      # libera a los hilos
        self._fin.wait()         # espera a que todos terminen las n generaciones
        if self._error is not None:
            raise RuntimeError(f"Un hilo falló: {self._error!r}") from self._error

    def step(self):
        self.run(1)

    def snapshot(self):
        return self._exportar()

    def close(self):
        if self._cerrado:
            return
        self._cerrado = True
        try:
            self._inicio.wait(timeout=5)          # despierta a los hilos para que salgan
        except threading.BrokenBarrierError:
            pass
        for hilo in self._hilos:
            hilo.join(timeout=5)

"""
v3_processes.py — V3: paralela con procesos (ProcessPoolExecutor), descomposición por
dominio en bandas de filas con FILAS FANTASMA.

Dependencias: engine_base, grid, rules, partition.
Herramientas [VISTO EN CLASE: Taller 1]: ProcessPoolExecutor, submit, as_completed.
Concepto [VISTO EN CLASE: Sesión de descomposición, Taller 2]: descomposición por dominio.

ESQUEMA POR GENERACIÓN:
    por cada banda: construir (banda + fila de arriba + fila de abajo)   [partition]
    submit(worker, banda_con_fantasmas) -> future
    recolectar con as_completed y ENSAMBLAR la nueva matriz
    (la sincronización es IMPLÍCITA: no se avanza hasta tener todos los resultados)

La función worker recibe una banda con fantasmas y devuelve SOLO su banda nueva
(sin fantasmas). Por dentro llama a rules.compute_rows sobre la banda local.

POOL PERSISTENTE: se crea en __init__ y se cierra en close(). Nunca por generación.

COSTO A DISCUTIR (aparece en el informe): cada generación copia datos al enviar
(pickle) y al devolver. En matrices pequeñas ese costo fijo domina => V3 puede ser
más lenta que V1 en 100x100. Es esperable. Mejora opcional: `shared_memory`
[FUERA DE CLASE], que evita copiar pero exige sincronizar las filas fantasma.

ERRORES COMUNES:
  - as_completed entrega en orden de FINALIZACIÓN, no de banda: guardar a qué banda
    corresponde cada future (p. ej. dict future -> índice) antes de ensamblar.
  - WINDOWS usa "spawn": el código de arranque debe ir bajo
    `if __name__ == "__main__":` y la función worker debe estar a NIVEL DE MÓDULO
    (para poder serializarse). Nada de pygame.init() ni código pesado al importar.
  - El pool crea los procesos bajo demanda: para que el arranque no contamine la
    primera medición, enviar una tarea trivial de "calentamiento" en __init__.

RENDIMIENTO ESPERADO: speedup real en 500x500 o más (cada proceso tiene su propio
GIL), sublineal por el costo de copia, y limitado por los núcleos FÍSICOS.
"""

import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from core import grid, partition, rules
from core.engine_base import Engine


def _calentar(_):
    """Tarea de calentamiento: devuelve el PID del proceso que la ejecutó."""
    time.sleep(0.1)       # mientras duerme, el pool crea otro proceso para la siguiente tarea
    return os.getpid()


def _worker_compute_band(band_with_ghosts):
    """Función del trabajador (a nivel de módulo, serializable).

    Entrada: banda con filas fantasma (h_banda + 2 filas).
    Salida: la banda nueva SIN fantasmas (h_banda filas).
    """
    n = len(band_with_ghosts)
    ancho = len(band_with_ghosts[0])
    # solo hacen falta filas de salida para las filas propias (1 .. n-2)
    salida = [None] + [bytearray(ancho) for _ in range(n - 2)] + [None]
    # rango (1, n-1): el kernel nunca sale de la banda, las fantasma ya hacen de envoltura
    rules.compute_rows(band_with_ghosts, salida, 1, n - 1)
    return partition.strip_ghost_rows(salida)


class ProcessEngine(Engine):
    name = "v3"

    def __init__(self, initial_grid, workers=1):
        self.actual = grid.copy(initial_grid)
        self.rangos = partition.row_ranges(len(self.actual), workers)
        self.p = len(self.rangos)
        self._cerrado = False
        # POOL PERSISTENTE: se crea una vez aquí y se cierra en close().
        self.pool = ProcessPoolExecutor(max_workers=self.p)
        # Calentamiento: el costo de arrancar procesos se paga aquí (setup), no en run().
        # Se repite hasta que respondan p PIDs distintos (= los p procesos ya están vivos);
        # con una sola ronda, algunos procesos seguían arrancando durante las primeras generaciones.
        pids = set()
        for _ in range(50):
            pids.update(self.pool.map(_calentar, range(self.p)))
            if len(pids) >= self.p:
                break

    def run(self, generations):
        if self._cerrado:
            raise RuntimeError("El motor ya fue cerrado")
        for _ in range(generations):
            futuros = {}
            for i, (r_start, r_end) in enumerate(self.rangos):
                banda = partition.with_ghost_rows(self.actual, r_start, r_end)   # copia = comunicación
                futuros[self.pool.submit(_worker_compute_band, banda)] = i
            # as_completed entrega por orden de FINALIZACIÓN: se guarda el índice de cada banda
            resultados = [None] * self.p
            for futuro in as_completed(futuros):
                resultados[futuros[futuro]] = futuro.result()
            # ensamblar en el orden de las bandas (la espera de todos es la sincronización)
            nueva = []
            for banda_nueva in resultados:
                nueva.extend(banda_nueva)
            self.actual = nueva

    def step(self):
        self.run(1)

    def snapshot(self):
        return grid.copy(self.actual)

    def close(self):
        if self._cerrado:
            return
        self._cerrado = True
        self.pool.shutdown(wait=True, cancel_futures=True)

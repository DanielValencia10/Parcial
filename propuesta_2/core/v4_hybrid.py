"""
v4_hybrid.py — V4 (OPCIONAL): híbrida SMP + SIMD = hilos + kernel NumPy vectorizado.

Dependencias: v2_threads (hereda hilos + Barrier), numpy.
Concepto [VISTO EN CLASE: Sesión VII y Taller 4, ejercicio integrador]: bloques por hilo
y NumPy dentro de cada hilo.

IDEA: igual que V2 (bandas de filas, hilos persistentes, Barrier), pero el cálculo de
cada banda NO usa bucles de Python: cuenta los vecinos sumando 8 vistas desplazadas
del arreglo (o equivalente) y aplica las reglas con operaciones vectorizadas.

RENDIMIENTO ESPERADO: NumPy libera el GIL en operaciones grandes sobre arreglos, así
que los hilos pueden aportar algo. La MAYOR ganancia viene de la vectorización (SIMD),
no de los hilos.

TRAMPA DE ANÁLISIS: NO compare V4 contra V1 en Python puro y lo llame "speedup de
paralelismo". Para aislar el efecto de los hilos use como base una versión
secuencial vectorizada (V4 con 1 hilo) y repórtelo por separado.
Con bandas pequeñas, el overhead de NumPy puede anular la ganancia.

Si V4 no se implementa, dejarlo mencionado como trabajo futuro en el informe.
"""

import numpy as np

from core.v2_threads import ThreadedEngine


class HybridEngine(ThreadedEngine):
    """Mismos hilos persistentes, bandas y Barrier que V2; solo cambia el KERNEL.

    Se hereda de ThreadedEngine a propósito: así la ÚNICA diferencia entre V2 y V4 es el
    kernel (Python puro vs NumPy) y la comparación aísla el efecto de la vectorización.
    Internamente la matriz es un ndarray uint8; se convierte desde/hacia la lista de
    bytearray del core SOLO en __init__ y snapshot (nunca dentro de run).
    """
    name = "v4"

    def _preparar_estado(self, initial_grid):
        self.actual = np.array(initial_grid, dtype=np.uint8)      # np.array COPIA
        self.siguiente = np.zeros_like(self.actual)

    def _calcular(self, r_start, r_end):
        # banda + fila de arriba + fila de abajo, y una columna extra a cada lado, todo en
        # ceros por defecto: lo que cae fuera de la matriz es "muerto" (esquinas incluidas).
        h, w = self.actual.shape
        ext = np.zeros((r_end - r_start + 2, w + 2), dtype=np.uint8)
        lo = max(r_start - 1, 0)                  # primera fila real que existe
        hi = min(r_end + 1, h)                    # una pasada de la última fila real
        ext[lo - (r_start - 1):hi - (r_start - 1), 1:w + 1] = self.actual[lo:hi]
        # 8 vistas desplazadas sumadas = vecinos vivos de cada celda de la banda
        vecinos = (ext[:-2, :-2] + ext[:-2, 1:-1] + ext[:-2, 2:] +
                   ext[1:-1, :-2] +                  ext[1:-1, 2:] +
                   ext[2:, :-2] + ext[2:, 1:-1] + ext[2:, 2:])
        viva = ext[1:-1, 1:-1]
        # nace (muerta con 3) o sobrevive (viva con 2 o 3): cada hilo escribe SOLO su banda
        self.siguiente[r_start:r_end] = (vecinos == 3) | ((vecinos == 2) & (viva == 1))

    def _exportar(self):
        return [bytearray(fila.tobytes()) for fila in self.actual]

"""
v5_mpi.py — V5: paralela con MPI (mpi4py). Alternativa a Threads que permite el enunciado
("Procesamiento por Mensajes (MPI)"). Se elige con config.MODO_PARALELO = "mpi" o la tecla 5.

Dependencias: engine_base, partition, registry, mpi4py y el runtime MS-MPI (Windows).
Concepto: descomposición por dominio en bandas de filas (igual que V2/V3) pero SIN memoria
compartida: cada proceso tiene su banda y se comunican solo con mensajes.

ESQUEMA:
    padre (GUI / benchmark / tests)                workers (core/mpi_worker.py)
    ───────────────────────────────                ─────────────────────────────
    __init__: Spawn de p workers  ───────────────► arrancan, esperan órdenes
              envía a cada uno su banda (init)
    run(n):   envía ("run", n)    ───────────────► n veces: intercambio de bordes
              espera p confirmaciones                        con vecinos + cómputo
    snapshot: pide ("get") y ensambla las bandas
    close:    ("stop") y Disconnect

CÓMO LANZAR: MS-MPI solo permite Spawn si el proceso padre arranca bajo mpiexec:
    mpiexec -n 1 python -m gui.app
    mpiexec -n 1 python -m benchmark.run_benchmark --versiones 5
    mpiexec -n 1 python -m tests.verify_correctness
Sin mpiexec, crear el motor lanza EngineUnavailable con este mismo aviso (la GUI no se cae).

COMPARACIÓN CON V3: V3 reenvía cada generación la banda entera (pickle) a un pool; V5 deja
la banda en el worker y solo intercambia 2 filas por worker y generación. El costo fijo de
V5 es arrancar los procesos (spawn) y la latencia de los mensajes.
"""

import atexit
import os
import sys

from mpi4py import MPI

from core import partition
from core.engine_base import Engine
from core.registry import EngineUnavailable

_WORKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mpi_worker.py")


class MPIEngine(Engine):
    name = "v5"

    def __init__(self, initial_grid, workers=1):
        self._cerrado = True        # hasta que el Spawn funcione, close() no hace nada
        self.h = len(initial_grid)
        self.w = len(initial_grid[0])
        self.rangos = partition.row_ranges(self.h, workers)
        self.p = len(self.rangos)
        try:
            self.inter = MPI.COMM_SELF.Spawn(sys.executable, args=[_WORKER], maxprocs=self.p)
        except MPI.Exception as exc:
            # mensaje corto: se muestra en el panel de la GUI (el detalle va en __cause__)
            raise EngineUnavailable("V5 (MPI): lanzar con  mpiexec -n 1 python -m <modulo>") from exc
        self._cerrado = False
        atexit.register(self.close)        # si el programa termina sin close(), no quedan workers vivos

        # Reparto inicial: cada worker recibe SOLO su banda (setup, no se cronometra en run()).
        for i, (r_start, r_end) in enumerate(self.rangos):
            plano = b"".join(initial_grid[r_start:r_end])
            self.inter.send(("init", self.w, plano), dest=i)
        self._esperar_confirmaciones()

    def _esperar_confirmaciones(self):
        for i in range(self.p):
            respuesta = self.inter.recv(source=i)
            if isinstance(respuesta, tuple) and respuesta[0] == "error":
                raise RuntimeError(f"El worker MPI {i} falló:\n{respuesta[1]}")

    def run(self, generations):
        if self._cerrado:
            raise RuntimeError("El motor ya fue cerrado")
        if generations <= 0:
            return
        for i in range(self.p):
            self.inter.send(("run", generations), dest=i)
        self._esperar_confirmaciones()      # barrera implícita: nadie sigue hasta que todos terminen

    def step(self):
        self.run(1)

    def snapshot(self):
        if self._cerrado:
            raise RuntimeError("El motor ya fue cerrado")
        for i in range(self.p):
            self.inter.send(("get",), dest=i)
        filas = []
        for i in range(self.p):
            plano = self.inter.recv(source=i)
            if isinstance(plano, tuple) and plano[0] == "error":
                raise RuntimeError(f"El worker MPI {i} falló:\n{plano[1]}")
            filas.extend(bytearray(plano[k:k + self.w]) for k in range(0, len(plano), self.w))
        return filas

    def close(self):
        if self._cerrado:
            return
        self._cerrado = True
        try:
            for i in range(self.p):
                self.inter.send(("stop",), dest=i)
            self.inter.Disconnect()
        except MPI.Exception:
            pass

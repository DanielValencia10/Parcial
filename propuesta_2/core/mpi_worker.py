"""
mpi_worker.py — Programa que ejecuta CADA proceso MPI de V5 (lo lanza v5_mpi.MPIEngine).

NO se ejecuta a mano. El proceso principal hace MPI.COMM_SELF.Spawn(...) de este archivo.

Qué hace cada worker (modelo de MENSAJES, sin memoria compartida):
  1. Recibe del padre SU banda de filas (init) y la guarda en memoria local.
  2. Por cada generación:
       a) COMUNICACIÓN: intercambia con sus vecinos SOLO las filas de borde
          (Sendrecv entre vecinos; los workers de los extremos no tienen vecino por un lado:
          MPI.PROC_NULL = "no enviar / no recibir", y su fantasma queda en ceros = fuera
          de la matriz, frontera muerta):
            - envía su primera fila al worker de arriba y recibe del de abajo su fila fantasma inferior
            - envía su última fila al worker de abajo y recibe del de arriba su fila fantasma superior
       b) CÓMPUTO: rules.compute_rows sobre [fantasma_arriba] + banda + [fantasma_abajo]
  3. A petición ("get") devuelve su banda al padre; con "stop" termina.

Se intercambian 2 filas por worker y generación (no la banda completa): ese es el costo de
comunicación de MPI. A diferencia de V3 (que reenvía las bandas enteras cada generación),
aquí cada worker conserva sus datos entre generaciones.
"""

import os
import sys
import traceback

# el worker se ejecuta como script: hay que poner la raíz del proyecto en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mpi4py import MPI          # noqa: E402

from core import rules          # noqa: E402

TAG_ARRIBA = 1
TAG_ABAJO = 2


def _generacion(comm, banda, arriba, abajo, ancho):
    """Una generación de la banda local: intercambio de bordes + cómputo."""
    fantasma_abajo = bytearray(ancho)
    fantasma_arriba = bytearray(ancho)
    # mi primera fila viaja al vecino de arriba; recibo la primera fila del de abajo
    comm.Sendrecv(banda[0], dest=arriba, sendtag=TAG_ARRIBA,
                  recvbuf=fantasma_abajo, source=abajo, recvtag=TAG_ARRIBA)
    # mi última fila viaja al vecino de abajo; recibo la última fila del de arriba
    comm.Sendrecv(banda[-1], dest=abajo, sendtag=TAG_ABAJO,
                  recvbuf=fantasma_arriba, source=arriba, recvtag=TAG_ABAJO)
    extendida = [fantasma_arriba] + banda + [fantasma_abajo]
    salida = [None] + [bytearray(ancho) for _ in banda] + [None]
    rules.compute_rows(extendida, salida, 1, len(extendida) - 1)
    return salida[1:-1]


def main():
    padre = MPI.Comm.Get_parent()
    comm = MPI.COMM_WORLD                      # el mundo de los workers entre sí
    rango, tamano = comm.Get_rank(), comm.Get_size()
    arriba = rango - 1 if rango > 0 else MPI.PROC_NULL            # el 0 no tiene vecino arriba
    abajo = rango + 1 if rango < tamano - 1 else MPI.PROC_NULL    # el último no tiene vecino abajo
    ancho = 0
    banda = []
    try:
        while True:
            orden = padre.recv(source=0)
            if orden[0] == "init":
                _, ancho, plano = orden
                banda = [bytearray(plano[i:i + ancho]) for i in range(0, len(plano), ancho)]
                padre.send("ok", dest=0)
            elif orden[0] == "run":
                for _ in range(orden[1]):
                    banda = _generacion(comm, banda, arriba, abajo, ancho)
                padre.send("ok", dest=0)
            elif orden[0] == "get":
                padre.send(b"".join(banda), dest=0)
            elif orden[0] == "stop":
                break
    except Exception:                           # noqa: BLE001 - se informa al padre
        padre.send(("error", traceback.format_exc()), dest=0)
    finally:
        padre.Disconnect()


if __name__ == "__main__":
    main()

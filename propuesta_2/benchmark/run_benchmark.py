"""
run_benchmark.py — Mide el rendimiento SIN GUI y escribe results/tiempos.csv.

Ejecutar desde la raíz:  python -m benchmark.run_benchmark
Dependencias: core.*, config, hardware_info. NUNCA importa gui.

QUÉ VERSIONES SE MIDEN (de mayor a menor prioridad):
  1. --versiones 1,2,3        lista explícita
  2. --modo hilos|procesos|mpi   V1 + la versión de ese modo (interruptor de config.MODO_PARALELO)
  3. config.VERSIONES_BENCHMARK  (lista con líneas comentables)
  V5 (MPI) exige mpiexec:   mpiexec -n 1 python -m benchmark.run_benchmark --versiones 5

PLAN DE MEDICIÓN:
  - Tamaños: config.TAMANOS; trabajadores: config.TRABAJADORES; versiones: V1..V5.
  - Generaciones fijas (config.GENERACIONES); config.REPETICIONES repeticiones por
    configuración; se reporta la MEDIANA (statistics.median) en make_plots.
  - Misma semilla (config.SEMILLA) para todo: mismo estado inicial en todas las pruebas.

QUÉ SE CRONOMETRA (con time.perf_counter, Taller 1):
  - SOLO engine.run(G). NO se incluye crear la matriz ni escribir el CSV.
  - El costo de crear hilos / arrancar el pool o los procesos MPI se mide APARTE (columna
    tiempo_setup_s) y se reporta por separado: es overhead real, pero no es "cómputo".
  - Antes de medir: calentamiento (run(1) sin cronometrar en cada motor).

BASE DEL SPEEDUP: V1. Nunca V2/V3 con 1 trabajador. (V4 tiene su propia base, ver make_plots.)

FORMATO DEL CSV (una fila por repetición):
    version,tamano,trabajadores,generaciones,repeticion,tiempo_setup_s,tiempo_computo_s

Otras opciones: --tamanos 100,500  --trabajadores 1,4  --generaciones 5  --repeticiones 1
                --salida results/piloto.csv  --reiniciar (borra el CSV antes de empezar)
Por defecto se AGREGA al CSV (así V5 se mide aparte sin borrar lo demás).

Windows: todo bajo `if __name__ == "__main__":` (V3 y V5 usan "spawn").
Cerrar otras aplicaciones pesadas mientras se mide; anotar el hardware (hardware_info).
"""

import argparse
import csv
import os
import time

import config
from benchmark import hardware_info
from core import grid
from core.registry import EngineUnavailable, load_engine_class, version_de_modo

RUTA_CSV = os.path.join("results", "tiempos.csv")
CABECERA = ["version", "tamano", "trabajadores", "generaciones", "repeticion",
            "tiempo_setup_s", "tiempo_computo_s"]


def run_one(version_cls, size, workers, generations, initial_grid=None):
    """Mide UNA ejecución.

    Entradas: clase del motor, tamaño, trabajadores, generaciones (y la matriz inicial si ya
              existe, para no regenerarla en cada repetición).
    Salida: (tiempo_setup_s, tiempo_computo_s).
    """
    if initial_grid is None:
        initial_grid = grid.new_grid(size, size)
        grid.randomize(initial_grid, config.SEMILLA, config.DENSIDAD)

    t0 = time.perf_counter()
    motor = version_cls(initial_grid, workers)         # crea hilos / pool / procesos MPI
    tiempo_setup = time.perf_counter() - t0
    try:
        motor.run(1)                                   # calentamiento (no se cronometra)
        t1 = time.perf_counter()
        motor.run(generations)                         # LO ÚNICO QUE SE CRONOMETRA
        tiempo_computo = time.perf_counter() - t1
    finally:
        motor.close()                                  # siempre, aunque falle algo
    return tiempo_setup, tiempo_computo


def _preparar_csv(ruta, reiniciar):
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    if reiniciar or not os.path.exists(ruta) or os.path.getsize(ruta) == 0:
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(CABECERA)


def _versiones_a_medir(args):
    if args.versiones:
        return [int(v) for v in args.versiones.split(",")]
    if args.modo:
        return sorted({1, version_de_modo(args.modo)})
    return list(config.VERSIONES_BENCHMARK)


def run_all(versiones=None, tamanos=None, trabajadores=None, generaciones=None,
            repeticiones=None, ruta_csv=RUTA_CSV, reiniciar=False):
    """Barre tamaños x versiones x trabajadores x repeticiones y escribe el CSV.

    Crea la cabecera si el archivo no existe. Imprime progreso para poder
    detectar una configuración demasiado lenta.
    """
    versiones = versiones or list(config.VERSIONES_BENCHMARK)
    tamanos = tamanos or config.TAMANOS
    trabajadores = trabajadores or config.TRABAJADORES
    generaciones = generaciones or config.GENERACIONES
    repeticiones = repeticiones or config.REPETICIONES

    _preparar_csv(ruta_csv, reiniciar)
    inicio_total = time.perf_counter()
    print(f"Versiones {versiones} | tamaños {tamanos} | trabajadores {trabajadores} | "
          f"G={generaciones} | repeticiones={repeticiones} | salida={ruta_csv}", flush=True)

    for size in tamanos:
        matriz = grid.new_grid(size, size)
        grid.randomize(matriz, config.SEMILLA, config.DENSIDAD)    # misma semilla para todo
        for v in versiones:
            try:
                clase = load_engine_class(v)
            except EngineUnavailable as exc:
                print(f"SALTADO V{v}: {exc}", flush=True)
                continue
            for p in ([1] if v == 1 else trabajadores):            # V1 ignora los trabajadores
                tiempos = []
                for rep in range(1, repeticiones + 1):
                    try:
                        setup, computo = run_one(clase, size, p, generaciones, matriz)
                    except EngineUnavailable as exc:
                        print(f"SALTADO V{v}: {exc}", flush=True)
                        break
                    tiempos.append(computo)
                    time.sleep(0.3)                # deja morir los procesos anteriores antes de la siguiente corrida
                    with open(ruta_csv, "a", newline="", encoding="utf-8") as f:
                        csv.writer(f).writerow([clase.name, size, p, generaciones, rep,
                                                f"{setup:.6f}", f"{computo:.6f}"])
                if tiempos:
                    mediana = sorted(tiempos)[len(tiempos) // 2]
                    print(f"[{time.perf_counter() - inicio_total:7.1f}s] V{v} {size}x{size} p={p:<2}"
                          f"  mediana {mediana:8.3f}s  ({generaciones} gen)", flush=True)
                else:
                    break                                           # versión no disponible
    print(f"Terminado en {time.perf_counter() - inicio_total:.1f}s", flush=True)


def main():
    ap = argparse.ArgumentParser(description="Benchmark del Juego de la Vida (sin GUI)")
    ap.add_argument("--versiones", help="p. ej. 1,2,3 (tiene prioridad sobre --modo)")
    ap.add_argument("--modo", choices=["hilos", "procesos", "mpi"],
                    help="mide V1 + la versión de ese modo")
    ap.add_argument("--tamanos", help="p. ej. 100,500,1000")
    ap.add_argument("--trabajadores", help="p. ej. 1,2,4,8")
    ap.add_argument("--generaciones", type=int)
    ap.add_argument("--repeticiones", type=int)
    ap.add_argument("--salida", default=RUTA_CSV)
    ap.add_argument("--reiniciar", action="store_true", help="borra el CSV antes de empezar")
    args = ap.parse_args()

    def lista(texto):
        return [int(x) for x in texto.split(",")] if texto else None

    hardware_info.save()          # deja results/hardware.txt actualizado junto a las mediciones
    run_all(_versiones_a_medir(args), lista(args.tamanos), lista(args.trabajadores),
            args.generaciones, args.repeticiones, args.salida, args.reiniciar)


if __name__ == "__main__":
    main()

"""
registry.py — Único lugar donde se listan las versiones (V1..V5) y cómo cargarlas.

Dependencias: ninguna al importar (las versiones se importan BAJO DEMANDA).
Lo usan: gui.app, benchmark.run_benchmark, tests.verify_correctness, tests.test_patterns.

Así, si falta una librería (p. ej. mpi4py para V5), solo esa versión queda "no disponible"
y todo lo demás sigue funcionando. Para añadir una versión basta una línea en ENGINES.

INTERRUPTOR HILOS / PROCESOS / MPI: ver MODOS y config.MODO_PARALELO.
"""

import importlib

# versión -> (módulo, clase)
ENGINES = {
    1: ("core.v1_sequential", "SequentialEngine"),
    2: ("core.v2_threads", "ThreadedEngine"),
    3: ("core.v3_processes", "ProcessEngine"),
    4: ("core.v4_hybrid", "HybridEngine"),
    5: ("core.v5_mpi", "MPIEngine"),
}

# Modo de paralelismo -> versión que lo implementa (el "parámetro" para decidir cuál usar).
MODOS = {
    "hilos": 2,       # Threads (threading + Barrier)
    "procesos": 3,    # multiprocessing (ProcessPoolExecutor + filas fantasma)
    "mpi": 5,         # MPI (mpi4py)
}

# Etiquetas legibles (GUI, tablas de resultados).
ETIQUETAS = {
    1: "secuencial",
    2: "hilos + Barrier",
    3: "procesos + filas fantasma",
    4: "hilos + NumPy",
    5: "MPI (mpi4py)",
}


class EngineUnavailable(Exception):
    """La versión pedida no se pudo cargar o iniciar."""


def load_engine_class(version):
    """Importa y devuelve la clase del motor de `version`. Lanza EngineUnavailable si no se puede."""
    module_name, class_name = ENGINES[version]
    try:
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as exc:
        raise EngineUnavailable(f"V{version} no disponible: {exc}") from exc


def version_de_modo(modo):
    """Traduce 'hilos' | 'procesos' | 'mpi' a su número de versión."""
    if modo not in MODOS:
        raise ValueError(f"Modo desconocido: {modo!r}. Opciones: {', '.join(MODOS)}")
    return MODOS[modo]

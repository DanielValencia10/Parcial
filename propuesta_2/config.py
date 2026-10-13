"""
config.py — Constantes ÚNICAS del proyecto.

Todas las versiones (V1..V4), la GUI, el benchmark y los tests importan de aquí.
Así se garantiza que usan la MISMA frontera, la MISMA semilla y los MISMOS parámetros.
Nada de "números mágicos" repartidos por el código.

Dependencias: ninguna.
"""

# --- Reglas del juego / estado inicial ---------------------------------------
# DECISIÓN TOMADA: "muerta" (todo lo que queda FUERA de la matriz cuenta como celda muerta;
# una celda del borde simplemente tiene menos vecinos). El enunciado no define el borde.
# Es la ÚNICA que implementa el kernel de core/rules.py, y la usan TODAS las versiones.
# (Antes se usó "toroidal"; se cambió a petición del grupo. Ya no hay interruptor para eso.)
FRONTERA = "muerta"

# --- INTERRUPTOR: ¿qué paralelismo se usa? -------------------------------------
# "hilos"    -> V2: threading + Barrier        (lo que el enunciado llama Threads)
# "procesos" -> V3: ProcessPoolExecutor + filas fantasma
# "mpi"      -> V5: mpi4py (hay que lanzar con:  mpiexec -n 1 python -m ...)
# Lo lee la GUI (versión con la que arranca) y los scripts que no reciben --modo.
MODO_PARALELO = "hilos"

SEMILLA = 12345          # Misma semilla => mismo estado inicial en todas las versiones
DENSIDAD = 0.30          # Fracción aproximada de celdas vivas al inicio

# --- Benchmark ---------------------------------------------------------------
TAMANOS = [100, 500, 1000]        # Del enunciado. Opcional: agregar 2000
TRABAJADORES = [1, 2, 4, 8, 16]   # Hilos (V2, V4) o procesos (V3, V5). Equipo: 8 físicos / 16 lógicos
REPETICIONES = 7                  # Se reporta la MEDIANA (robusta ante una corrida atípica)

# Versiones que mide el benchmark. COMENTAR / DESCOMENTAR según lo que se quiera medir
# (también se puede sobrescribir con:  --versiones 1,2,3  o  --modo mpi).
# V5 (MPI) se mide APARTE porque exige lanzar con mpiexec:
#     mpiexec -n 1 python -m benchmark.run_benchmark --versiones 5
VERSIONES_BENCHMARK = [
    1,      # secuencial (base del speedup)
    2,      # hilos + Barrier
    3,      # procesos + filas fantasma
    4,      # hilos + NumPy (su base es V4 con 1 hilo)
    # 5,    # MPI  (requiere mpiexec -n 1)
]

# CALIBRADO: V1 (Python puro) tarda ~0.19 s por generación en 1000x1000, así que
# 50 generaciones ~ 10 s por corrida de V1: suficiente para medir bien y razonable.
GENERACIONES = 50

# --- GUI ---------------------------------------------------------------------
GUI_TAMANO = 5         # La GUI NO es para medir tiempos; matriz moderada
GUI_FPS = 10
GUI_TRABAJADORES = 4      # trabajadores con los que arranca la GUI (debe estar en TRABAJADORES)

# Juego de la Vida paralelo — Propuesta 2 (Python)

Parcial I «Paralelismo en Acción». Todo en Python: GUI con pygame, gráficas con matplotlib.
Paralelismo con **Threads** (V2, V4), **procesos** (V3) y **MPI** (V5); se elige con un parámetro.

## Qué problema es
Paralelismo de datos con cómputo tipo *stencil*. El bucle de generaciones es serial
(trampa serial); dentro de cada generación las celdas son independientes.
**Estrategia:** descomposición por dominio en bandas de filas + doble búfer + sincronización por generación.

## Versiones
| Versión | Archivo | Herramienta | Rendimiento observado (ver `results/resumen.md`) |
|---|---|---|---|
| V1 | `core/v1_sequential.py` | Python puro | Base de comparación |
| V2 | `core/v2_threads.py` | `threading` + `Barrier` | ≈ 1× o menor (GIL) — resultado válido |
| V3 | `core/v3_processes.py` | `ProcessPoolExecutor` + filas fantasma | Speedup real en tamaños grandes |
| V4 | `core/v4_hybrid.py` | hilos + NumPy (hereda de V2) | Ganancia sobre todo por SIMD |
| V5 | `core/v5_mpi.py` + `core/mpi_worker.py` | `mpi4py` (MS-MPI), `Sendrecv` de bordes | Speedup real; sin copiar la banda cada generación |

## INTERRUPTOR: ¿hilos, procesos o MPI?
Un solo lugar: `config.py`.
```python
MODO_PARALELO = "hilos"          # "hilos" (V2) | "procesos" (V3) | "mpi" (V5)
VERSIONES_BENCHMARK = [1, 2, 3, 4,   # comentar/descomentar líneas
                       # 5,           # MPI (requiere mpiexec -n 1)
                       ]
```
- **GUI:** arranca con la versión de `MODO_PARALELO`; las teclas `1`–`5` la cambian en vivo.
- **Benchmark:** `--modo hilos|procesos|mpi` (mide V1 + esa versión) o `--versiones 1,2,5`; sin
  argumentos usa `VERSIONES_BENCHMARK`. La línea de comandos manda sobre `config.py`.
- Las versiones se registran en `core/registry.py` (`ENGINES`, `MODOS`). Si falta una librería
  (p. ej. mpi4py) solo esa versión queda «no disponible»: el resto sigue funcionando.

## Estructura
```
core/        grid, rules, partition, patterns, engine_base, registry, v1..v5, mpi_worker
gui/         pygame (usa core, no lo modifica)
benchmark/   mide sin GUI -> results/tiempos.csv, results/hardware.txt
plots/       make_plots.py -> results/figures/ y results/resumen.md
tests/       correctitud: versiones vs V1, patrones, reparto de filas
results/     tiempos.csv, hardware.txt, resumen.md, figures/
informe/     informe.md y notas_sustentacion.md
config.py    constantes únicas (frontera, semilla, tamaños, interruptor, etc.)
```

## Instalación (Windows)
```
pip install -r requirements.txt
```
- **pygame:** si `pip install pygame` falla (Python 3.14 aún no tiene instalador), `requirements.txt`
  usa `pygame-ce` (mismo `import pygame`).
- **MPI (solo para V5):** instalar el runtime MS-MPI (`winget install Microsoft.msmpi`) y `pip install mpi4py`.
  Sin esto V5 aparece como «no disponible» y todo lo demás funciona.

## Cómo ejecutar (desde esta carpeta, siempre con `python -m ...`)
```
python -m tests.test_partition
python -m tests.test_patterns            # V1..V4 (V5 se salta si no hay mpiexec)
python -m tests.verify_correctness       # SIEMPRE antes de medir
python -m gui.app                        # GUI (V1..V4)
python -m benchmark.run_benchmark        # benchmark (sin GUI) -> results/tiempos.csv
python -m plots.make_plots               # gráficas + results/resumen.md
```
**V5 (MPI)** exige que el proceso principal arranque bajo `mpiexec` (MS-MPI no permite `Spawn` sin él):
```
mpiexec -n 1 python -m gui.app
mpiexec -n 1 python -m tests.verify_correctness --versiones 5
mpiexec -n 1 python -m tests.test_patterns --versiones 5
mpiexec -n 1 python -m benchmark.run_benchmark --versiones 5      # se AGREGA al CSV
```
(`mpiexec` está en `C:\Program Files\Microsoft MPI\Bin`; si la terminal no lo encuentra, abrir una nueva
o usar la ruta completa.)

## GUI
`python -m gui.app` — solo usa `core.grid`, `core.patterns`, `core.registry` y el contrato `Engine`
(`Engine(grid, workers)`, `step()`, `snapshot()`, `close()`). Si una versión no se puede cargar o iniciar,
pausa y lo muestra en el panel inferior en vez de caerse.

Teclas: `ESPACIO` iniciar/pausar · `N` paso · `R` aleatorio (semilla fija) · `S` semilla nueva ·
`C` limpiar · `1-5` versión · `↑/↓` trabajadores · `←/→` velocidad · `G` cuadrícula ·
`B`/`L` blinker/glider bajo el ratón · clic izq./der. pintar/borrar · `H` ayuda · `Esc` salir.

## Decisiones de diseño
- Matriz = lista de `bytearray` (0/1) en todo el core; V4 y la GUI la convierten a NumPy en los bordes.
- Frontera **muerta** en todas las versiones: lo que queda fuera de la matriz cuenta como celda muerta
  (una celda del borde tiene menos vecinos). El enunciado no define el borde; fue decisión del grupo.
  Las filas fantasma de las bandas de los extremos (V3, V5) son filas de ceros.
- Una sola regla (`core/rules.py`): el kernel por filas lo usan V1, V2, V3 y V5; V4 tiene el equivalente
  vectorizado. Los tests lo comparan contra la regla celda a celda del enunciado.
- Hilos / pool / procesos MPI se crean **una vez** (`__init__`), no por generación.

## Reglas de oro
- Primero **correctitud**, luego **medición**.
- El benchmark **nunca** abre la GUI.
- El speedup se calcula contra **V1** (V4 contra V4 con 1 hilo).
- Todo el código de arranque bajo `if __name__ == "__main__":` (Windows usa *spawn*).

## Marcas en los comentarios
`[VISTO EN CLASE: ...]` = apoyado en el material del curso.
`[FUERA DE CLASE]` = no se vio; es mínimo y está justificado (pygame, mpi4py, matplotlib).

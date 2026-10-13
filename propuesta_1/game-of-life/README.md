# Game of Life paralelo

Implementación secuencial y paralela (hilos) del Juego de la Vida de Conway, con GUI
y benchmark para comparar rendimiento.

**Decisiones:** Java · hilos (memoria compartida) · división por filas ·
fronteras: _(completar: toroidal o muertas)_

## Estructura

```
game-of-life/
├── src/
│   ├── core/          # lógica: Grid, Rules, Engine, Sequential, Parallel, Patterns
│   ├── gui/           # visualización (usa core, no lo modifica)
│   └── benchmark/     # mide sin GUI y escribe results/tiempos.csv
├── tests/             # correctitud: secuencial vs paralelo, blinker, glider
├── results/           # tiempos.csv
├── plots/             # plot_results.py -> gráficas PNG
└── informe/           # informe.md y hardware.md
```

Regla de oro: **GUI y benchmark usan el mismo `core`**, y el benchmark **nunca** corre con GUI.

## Compilar y ejecutar (desde la carpeta game-of-life)

```powershell
# Compilar todo a la carpeta out/
javac -d out (Get-ChildItem -Recurse src, tests -Filter *.java).FullName

# Tests de correctitud (correr SIEMPRE antes de medir)
java -cp out CorrectnessTest

# GUI
java -cp out gui.MainGui

# Benchmark: tamano hilos generaciones repeticiones
java -cp out benchmark.Benchmark 1000 4 100 5

# Gráficas
python plots/plot_results.py
```

## Orden de trabajo y responsables

| # | Tarea                                            | Responsable |
|---|--------------------------------------------------|-------------|
| 1 | Acordar lenguaje, bordes y API de `core`         | Todos       |
| 2 | `Grid`, `Rules`, `SequentialEngine`, `Patterns` + tests de patrones | A |
| 3 | `ParallelEngine`                                 | B           |
| 4 | GUI                                              | C           |
| 5 | Benchmark + CSV + gráficas                       | A y C       |
| 6 | Informe (cada uno su parte)                      | Todos       |

Cada archivo en `src/` tiene comentarios con la idea de cómo resolverlo y marcas `TODO`.
Primero **correctitud**, después **medición**; no optimizar antes de tiempo.

## Checklist para la sustentación

- [ ] ¿Por qué dividimos por filas?
- [ ] ¿Por qué no hay condiciones de carrera? (doble búfer + filas disjuntas)
- [ ] ¿Para qué sirven las barreras y cuánto cuestan?
- [ ] ¿Por qué 100x100 no mejora?
- [ ] ¿Qué dice la Ley de Amdahl de nuestros resultados?

# Notas para la sustentación

> Todos deben poder responder TODAS estas preguntas, no solo las de su módulo.
> Las respuestas ya traen los datos medidos (`results/resumen.md`); léanlas y reescríbanlas con sus palabras.

| Pregunta | Idea de respuesta | Datos propios medidos |
|---|---|---|
| ¿Por qué dividir por filas? | Memoria contigua (localidad de caché), frontera pequeña (2 filas por banda), reparto simple. Bloques 2D solo compensan con muchos trabajadores y complican esquinas. | Con 1000 columnas, cada banda intercambia 2 filas = 2000 celdas, frente a 250 000 que calcula (p=4). |
| ¿Por qué no hay condiciones de carrera? | Se lee de una matriz y se escribe en otra; cada trabajador escribe filas distintas ("vector independiente"). No hay Lock en el cómputo. | 24/24 configuraciones de V2 iguales a V1 en `verify_correctness`. |
| ¿Qué pasaría con una sola matriz? | Una celda ya actualizada contaminaría a su vecina; el resultado dependería del orden de ejecución (no determinista con hilos). | Por eso el doble búfer y el swap de referencias. |
| ¿Para qué sirve la Barrier? | Todos terminan de escribir la generación t+1 antes de que alguien la lea como "actual". La acción de la barrera hace el swap una sola vez. Cuesta espera. | En 100×100 la barrera/comunicación domina: V2 baja a 0,70× con 16 hilos. |
| ¿Por qué V2 no acelera? | GIL: un solo hilo ejecuta Python a la vez; más hilos = más contención y barreras. | Speedup 0,95–1,02 en 500×500 y 1000×1000 con 1–16 hilos; f estimada ≈ 1. |
| ¿Por qué V3 sí acelera, y cuándo no? | Cada proceso tiene su GIL; pero copiar/ensamblar datos tiene costo fijo que domina en matrices pequeñas. | 1000×1000: 4,4× con 8 procesos (6,5× con 16). 100×100: 1,3× como máximo y 0,77× con 16. |
| ¿Por qué la base es V1 y no V3 con 1 proceso? | V3 con 1 proceso ya paga overhead de comunicación; la base debe ser el mejor secuencial "sin paralelismo". | V3 con 1 proceso en 100×100: 0,77× (más lento que V1). |
| ¿Dónde haría falta un Lock? | En un contador compartido (celdas vivas); mejor evitarlo con parciales por trabajador y sumarlos al final. | `alive_count` es una reducción; no se paraleliza en el cómputo. |
| ¿Qué pasa con 1000 filas y 7 trabajadores? | 1000 // 7 = 142 y sobran 6: las 6 primeras bandas llevan 143 filas y la última 142. | `test_partition` lo verifica. |
| ¿Qué dice Amdahl de sus datos? | f ≈ (1/S − 1/p)/(1 − 1/p). Relacionarlo con empaquetado/ensamblado/swap y coordinación del padre. | 1000×1000: V5 f ≈ 0,03; V3 f ≈ 0,12; V2 f ≈ 1. Máximo teórico con 8 procesos ≈ 6,6× (V5) y 4,4× (V3); medido 6,56× y 4,39×. |
| ¿Por qué el pool es persistente? | Crear procesos/hilos cuesta; hacerlo por generación destruiría el rendimiento. | Arrancar 8 procesos tarda ≈ 7–8 s en Windows (spawn); una generación de 1000×1000 en V3 con 8 procesos ≈ 45 ms. |
| ¿Cómo verificaron correctitud? | Comparación con V1 tras N generaciones, filas no divisibles, p > h, blinker, glider en la frontera entre bandas, block (también en esquinas), y glider/blinker contra el borde comparados con el oráculo celda a celda. Además se rompió a propósito la fila fantasma y los tests fallaron. | 24/24 por versión (V2–V5), todos los patrones OK. |
| ¿Por qué Threads **y** MPI? | El enunciado pide uno; se hicieron ambos para comparar memoria compartida vs paso de mensajes con el mismo kernel; se elige con `config.MODO_PARALELO` / `--modo`. | V5 (MPI) 6,6× vs V3 4,4× con 8 procesos (1000×1000). |
| ¿Cómo funciona MPI aquí? | Cada worker conserva su banda; por generación intercambia solo 2 filas con sus vecinos (`Sendrecv`; los extremos usan `MPI.PROC_NULL` = borde muerto) y calcula. El padre solo coordina. | Sin `mpiexec` no hay `Spawn` en MS-MPI: se lanza con `mpiexec -n 1 python -m ...`. |
| ¿Por qué V5 supera a V3? (hipótesis) | V3 reenvía y ensambla las bandas desde el padre cada generación (parte serial repetida); V5 solo mueve 2 filas por worker. **No se aisló con una medición dedicada: decirlo como hipótesis.** | f: V5 ≈ 0,03 vs V3 ≈ 0,12 en 1000×1000. |
| ¿V4 mide paralelismo? | No solo: la vectorización (SIMD) domina; por eso tiene su propia base (V4 con 1 hilo). | V4(1 hilo) ya es 22–31× más rápida que V1; los hilos suman hasta 3,06× (4 hilos, 1000×1000) y se estancan en 2,4×. |
| ¿Por qué el speedup se estanca? | Hay 8 núcleos físicos y 16 lógicos (SMT); pasados los físicos, cada hilo extra rinde menos y suben comunicación y arranque. | V5 1000×1000: 6,6× (8) → 9,3× (16); eficiencia 0,82 → 0,58. |
| ¿Por qué 100×100 no mejora? | El trabajo por generación (≈ 2 ms) es comparable al costo de sincronizar/comunicar. | V3 máx. 1,33× y 0,77× con 16; V5 3,2× con 8 (eficiencia 0,41). |
| ¿Por qué borde muerto? | El enunciado no define el borde; fuera de la matriz = muertas es lo más directo. Importa: en un 5×5 de ejemplo cambian 6 celdas respecto a un borde toroidal. Misma frontera en todas las versiones, si no la comparación no vale. | Se prueba con un glider contra la esquina y blinkers pegados al borde, contra el oráculo celda a celda. |

## Dudas para el profesor
- ¿Se acepta `multiprocessing` (V3) como "Threads", o deben ser hilos reales? (V2 los cubre; V5 es MPI.)
- ¿El secuencial base debe ser Python puro o se permite NumPy? (Aquí la base es Python puro; V4 tiene su propia base.)
- ¿Hay tamaño máximo o tiempo máximo razonable para las pruebas?
- ¿Se aceptan `pygame` (se usa `pygame-ce`), `mpi4py` y `matplotlib`?
- ¿Formato/extensión del informe?
- ¿Qué se espera en el borde de la matriz? El enunciado no lo define: aquí se usó borde muerto (fuera = celdas muertas).
- ¿Política del curso sobre el uso de asistentes de IA y si debe declararse en el informe? (Este proyecto se completó con ayuda de un asistente de IA: conviene declararlo si la política lo exige.)

## Cómo mostrarlo en vivo (guion corto)
1. `python -m tests.verify_correctness` → "TODO OK" (V2–V4); con `mpiexec` para V5.
2. `python -m gui.app`: `R` aleatorio, `ESPACIO`, teclas `1`–`4` para comparar versiones, `↑/↓` trabajadores,
   `L` glider, clic para pintar. Con V3 y 100×100 la GUI puede ir más lenta que V1: es normal (overhead).
3. `mpiexec -n 1 python -m gui.app` y tecla `5` para MPI.
4. Mostrar `results/figures/speedup_vs_trabajadores.png` y explicarla con Amdahl y el GIL.

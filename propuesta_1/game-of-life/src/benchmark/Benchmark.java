package benchmark;

/**
 * BENCHMARK: se ejecuta SIN GUI y escribe resultados a results/tiempos.csv.
 *
 * Uso sugerido (por línea de comandos o con un barrido interno):
 *     java -cp out benchmark.Benchmark <tamano> <hilos> <generaciones> <repeticiones>
 *
 * Plan de medición (del plan de análisis):
 *   - Tamaños:   100, 500, 1000 (enunciado) + 2000 y/o 5000.
 *   - Hilos:     1, 2, 4, 8 ... hasta los núcleos de la máquina.
 *   - Generaciones fijas (ej. 100 o 500).
 *   - Varias repeticiones por configuración; luego mediana o promedio.
 *
 * Buenas prácticas de medición:
 *   - Usar System.nanoTime() (no currentTimeMillis).
 *   - Medir SOLO engine.run(...). No incluir creación del grid ni escritura del CSV.
 *   - WARM-UP: en Java el JIT optimiza tras unas ejecuciones; hacer 1-2 corridas
 *     descartadas antes de medir, o los primeros tiempos saldrán inflados.
 *   - Misma semilla en todas las configuraciones: el mismo estado inicial para todos.
 *   - Cerrar otras aplicaciones pesadas mientras se mide.
 *   - El tiempo "secuencial" (línea base del speedup) se mide con SequentialEngine,
 *     NO con ParallelEngine(1): este último paga overhead de hilos y barreras.
 *
 * Formato del CSV (una fila por repetición):
 *     motor,tamano,hilos,generaciones,repeticion,tiempo_ms
 *     sequential,1000,1,100,1,812.4
 *     parallel,1000,4,100,1,251.9
 *
 * El speedup y la eficiencia NO se calculan aquí: eso lo hace plots/plot_results.py.
 */
public class Benchmark {

    public static void main(String[] args) {
        // TODO 1: leer parámetros (o definir los arreglos de tamaños e hilos)
        // TODO 2: por cada configuración: warm-up, N repeticiones midiendo con nanoTime
        // TODO 3: anexar filas a results/tiempos.csv (crear cabecera si el archivo no existe)
    }
}

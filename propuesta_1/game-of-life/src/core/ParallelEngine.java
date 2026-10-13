package core;

/**
 * VERSIÓN PARALELA (hilos, memoria compartida).
 *
 * ESTRATEGIA: descomposición de dominio por FILAS.
 *   - Se parte la matriz en 'numThreads' rangos contiguos de filas.
 *   - Cada hilo calcula SU rango con Rules.computeRows(actual, siguiente, ini, fin).
 *   - Los bordes entre rangos se leen directamente (memoria compartida): no hay ghost rows.
 *
 * ESQUEMA POR GENERACIÓN (el corazón del informe):
 *
 *     cada hilo: computeRows(actual, siguiente, mi_ini, mi_fin)
 *     ── BARRERA 1 ──  (todos terminaron de escribir 'siguiente')
 *     UN solo hilo (ej. el 0): intercambia actual <-> siguiente
 *     ── BARRERA 2 ──  (todos ven el swap antes de empezar la siguiente generación)
 *
 * Pistas de implementación:
 *   - java.util.concurrent.CyclicBarrier(numThreads, accionOpcional). La acción de la
 *     barrera se ejecuta una sola vez por ciclo: sirve perfecto para hacer el swap
 *     y evitar la segunda barrera.
 *   - 'actual' y 'siguiente' deben ser compartidos y su swap visible para todos
 *     (campos volatile, o que el swap ocurra dentro de la acción de la barrera,
 *      que ya establece happens-before).
 *   - NO crear y destruir hilos en cada generación: crearlos UNA vez en run()
 *     (o usar un ExecutorService fijo) y que hagan el bucle de generaciones.
 *   - Esperar a que todos terminen (join / invokeAll) antes de devolver el resultado.
 *
 * BALANCE DE CARGA: repartir bien las filas sobrantes.
 *   Ej. 1000 filas / 7 hilos = 142 base, y 6 filas sobrantes: los primeros 6 hilos
 *   reciben 143. Un reparto ingenuo deja a un hilo con mucho más trabajo.
 *
 * CASO BORDE: si numThreads > rows, limitar el número de hilos.
 */
public class ParallelEngine implements Engine {

    private final int numThreads;

    public ParallelEngine(int numThreads) {
        // TODO: validar numThreads >= 1 y guardarlo
        this.numThreads = numThreads;
    }

    @Override
    public Grid run(Grid initial, int generations) {
        // TODO: crear hilos una vez, repartir rangos, bucle de generaciones con barrera
        throw new UnsupportedOperationException("TODO");
    }

    /**
     * Calcula el rango [inicio, fin) de filas del hilo 'threadId'.
     * Función pura y fácil de testear: pruébenla con 1000 filas y 7 hilos.
     */
    static int[] rowRange(int rows, int numThreads, int threadId) {
        // TODO: base = rows / numThreads; extra = rows % numThreads; ...
        throw new UnsupportedOperationException("TODO");
    }

    @Override
    public String name() { return "parallel-" + numThreads; }
}

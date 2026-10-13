package core;

/**
 * GRID: representación de la matriz de celdas (0 = muerta, 1 = viva).
 *
 * DECISIONES QUE HAY QUE TOMAR (y documentar en el informe):
 *  - Fronteras: ¿muertas o toroidales (se envuelven)? Elegir UNA y usarla igual
 *    en secuencial y paralelo. Sugerencia: toroidal con módulo ((r + rows) % rows).
 *  - Almacenamiento: un arreglo plano byte[rows * cols] por filas (row-major).
 *    Es más amigable con la caché que byte[][] y hace trivial repartir "rangos de filas".
 *    Índice de (r, c) = r * cols + c.
 *
 * QUIÉN LO USA: Rules, SequentialEngine, ParallelEngine, GUI, Benchmark y Tests.
 * NO debe depender de ninguno de ellos.
 */
public class Grid {

    private final int rows;
    private final int cols;
    private final byte[] cells;

    public Grid(int rows, int cols) {
        // TODO: guardar dimensiones y reservar el arreglo plano.
        throw new UnsupportedOperationException("TODO");
    }

    public int rows() { throw new UnsupportedOperationException("TODO"); }

    public int cols() { throw new UnsupportedOperationException("TODO"); }

    /** Devuelve el estado de la celda (r, c). Aquí (o en Rules) se aplica la política de frontera. */
    public byte get(int r, int c) { throw new UnsupportedOperationException("TODO"); }

    public void set(int r, int c, byte value) { throw new UnsupportedOperationException("TODO"); }

    /**
     * Inicialización aleatoria CON SEMILLA FIJA.
     * Importante: con la misma semilla, secuencial y paralelo deben partir del mismo estado.
     * Pista: java.util.Random(seed) y una densidad (ej. 0.3 = 30% de celdas vivas).
     */
    public void randomize(long seed, double density) {
        // TODO
        throw new UnsupportedOperationException("TODO");
    }

    /** Copia profunda. Útil para que los tests partan del mismo estado en ambas versiones. */
    public Grid copy() { throw new UnsupportedOperationException("TODO"); }

    /** Comparación celda a celda. La usan los tests (secuencial vs paralelo). */
    public boolean sameAs(Grid other) { throw new UnsupportedOperationException("TODO"); }

    /** Hash del contenido (ej. Arrays.hashCode). Alternativa rápida a sameAs para comparar. */
    public int contentHash() { throw new UnsupportedOperationException("TODO"); }

    /** Cuenta de celdas vivas. Útil para depurar y para mostrar en la GUI. */
    public int aliveCount() { throw new UnsupportedOperationException("TODO"); }
}

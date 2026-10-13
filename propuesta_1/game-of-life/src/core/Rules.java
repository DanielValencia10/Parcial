package core;

/**
 * RULES: la lógica del juego, escrita UNA SOLA VEZ.
 * Secuencial y paralelo llaman exactamente a estas funciones, así la comparación
 * de rendimiento es justa (lo único que cambia es quién recorre qué filas).
 *
 * Reglas del enunciado (Conway):
 *  1. Viva con < 2 vecinos vivos        -> muere (soledad)
 *  2. Viva con 2 o 3 vecinos vivos      -> sigue viva
 *  3. Viva con > 3 vecinos vivos        -> muere (sobrepoblación)
 *  4. Muerta con exactamente 3 vecinos  -> nace
 */
public final class Rules {

    private Rules() {}

    /**
     * Cuenta los vecinos vivos (8 direcciones) de la celda (r, c) en 'g'.
     * Aquí se implementa la política de bordes (toroidal o muerta).
     */
    public static int countNeighbors(Grid g, int r, int c) {
        // TODO
        throw new UnsupportedOperationException("TODO");
    }

    /** Aplica las 4 reglas: dado el estado actual y el número de vecinos, devuelve el nuevo estado. */
    public static byte nextState(byte current, int neighbors) {
        // TODO
        throw new UnsupportedOperationException("TODO");
    }

    /**
     * EL NÚCLEO REUTILIZABLE: calcula las filas [rowStart, rowEnd) de la siguiente
     * generación. Lee de 'from' y escribe SOLO en 'to' (doble búfer).
     *
     *  - Secuencial: lo llama una vez con (0, rows).
     *  - Paralelo:   cada hilo lo llama con SU rango de filas.
     *
     * Como cada hilo escribe en filas distintas de 'to' y solo LEE de 'from',
     * no hay condiciones de carrera ni hace falta mutex.
     */
    public static void computeRows(Grid from, Grid to, int rowStart, int rowEnd) {
        // TODO: doble bucle (filas del rango x todas las columnas)
        //       to.set(r, c, nextState(from.get(r, c), countNeighbors(from, r, c)));
        throw new UnsupportedOperationException("TODO");
    }
}

package core;

/**
 * VERSIÓN SECUENCIAL (línea base para medir el speedup).
 *
 * Idea:
 *   actual    = copia de initial
 *   siguiente = Grid vacío del mismo tamaño
 *   repetir 'generations' veces:
 *       Rules.computeRows(actual, siguiente, 0, rows)
 *       intercambiar las referencias actual <-> siguiente   (NO copiar celdas, solo swap)
 *   devolver actual
 *
 * Por qué doble búfer: si se escribe sobre la misma matriz que se lee, una celda ya
 * actualizada contamina el cálculo de su vecina. Es el error más común.
 */
public class SequentialEngine implements Engine {

    @Override
    public Grid run(Grid initial, int generations) {
        // TODO
        throw new UnsupportedOperationException("TODO");
    }

    @Override
    public String name() { return "sequential"; }
}

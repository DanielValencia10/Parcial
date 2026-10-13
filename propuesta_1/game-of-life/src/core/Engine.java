package core;

/**
 * ENGINE: contrato común de las dos versiones (secuencial y paralela).
 * La GUI, el benchmark y los tests dependen de esta interfaz, no de la clase concreta.
 * Así se puede cambiar de motor sin tocar nada más.
 */
public interface Engine {

    /**
     * Avanza 'generations' generaciones a partir de 'initial' y devuelve el estado final.
     * NO debe modificar 'initial' (trabajar sobre copias / doble búfer).
     */
    Grid run(Grid initial, int generations);

    /** Nombre para logs y CSV, ej. "sequential" o "parallel". */
    String name();
}

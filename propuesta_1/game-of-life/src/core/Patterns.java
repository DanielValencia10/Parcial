package core;

/**
 * PATRONES CONOCIDOS para verificar correctitud (los usan tests/ y opcionalmente la GUI).
 * Cada método coloca el patrón en el Grid recibido, con su esquina en (r, c).
 */
public final class Patterns {

    private Patterns() {}

    /**
     * BLINKER: oscilador de periodo 2. Tres celdas en línea.
     * Test: tras 1 generación cambia de horizontal a vertical; tras 2 vuelve al original.
     */
    public static void placeBlinker(Grid g, int r, int c) {
        // TODO
    }

    /**
     * GLIDER: se desplaza 1 celda en diagonal cada 4 generaciones.
     * Test: tras 4 generaciones, el patrón es el mismo pero movido (+1, +1).
     * OJO: con fronteras muertas choca y se deforma; con toroidal da la vuelta.
     */
    public static void placeGlider(Grid g, int r, int c) {
        // TODO
    }

    /** Opcional: BLOCK (vida estable) sirve como test trivial de "no cambia nunca". */
    public static void placeBlock(Grid g, int r, int c) {
        // TODO
    }
}

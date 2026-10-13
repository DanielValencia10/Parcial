import core.*;

/**
 * TESTS DE CORRECTITUD. Se corren ANTES de medir rendimiento.
 * Sin framework (main simple con asserts propios) para no depender de JUnit;
 * si prefieren JUnit, la estructura de los casos es la misma.
 *
 * Casos a cubrir:
 *
 *  1. SECUENCIAL == PARALELO
 *     Mismo grid aleatorio (misma semilla), N generaciones, para varios tamaños
 *     (incluya uno NO divisible entre los hilos, ej. 1000 filas y 7 hilos) y varios
 *     números de hilos (1, 2, 3, 4, 7, 8). Comparar con Grid.sameAs() o contentHash().
 *
 *  2. BLINKER (periodo 2)
 *     Colocar el blinker, avanzar 1 generación -> debe estar rotado;
 *     avanzar 2 -> debe ser igual al original. Probarlo en ambos motores.
 *
 *  3. GLIDER
 *     Avanzar 4 generaciones -> mismo patrón desplazado (+1, +1)
 *     (con fronteras toroidales y espacio suficiente para que no choque).
 *
 *  4. BLOCK (opcional) -> nunca cambia.
 *
 *  5. BORDES DE REPARTO (opcional)
 *     ParallelEngine.rowRange: los rangos deben cubrir [0, rows) sin huecos ni solapes.
 *
 * Reporte: imprimir "OK"/"FALLO" por caso y terminar con exit code != 0 si algo falla.
 */
public class CorrectnessTest {

    public static void main(String[] args) {
        // TODO: llamar a cada caso y llevar la cuenta de fallos
    }

    // TODO: static boolean testSequentialEqualsParallel()
    // TODO: static boolean testBlinker(Engine e)
    // TODO: static boolean testGlider(Engine e)
}

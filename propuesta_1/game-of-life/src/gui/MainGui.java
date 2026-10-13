package gui;

/**
 * GUI: ventana principal. USA el core, NUNCA lo modifica.
 *
 * Qué debe tener (simple es suficiente):
 *   - Un GridPanel con la cuadrícula.
 *   - Botones: Iniciar / Pausar / Paso a paso / Aleatorio / Limpiar.
 *   - (Opcional) Selector de motor: secuencial o paralelo + número de hilos.
 *   - (Opcional) Contador de generación y de celdas vivas; clic para pintar celdas.
 *
 * Pistas:
 *   - Usar javax.swing.Timer para avanzar generaciones: corre en el hilo de eventos
 *     (EDT) y no congela la ventana. Si el cálculo fuera pesado, usar SwingWorker.
 *   - Cada tick: grid = engine.run(grid, 1); panel.repaint();
 *   - Para la GUI conviene un tamaño moderado (ej. 100x100); no es para medir tiempos.
 *   - La GUI jamás se usa en el benchmark: dibujar contamina los tiempos.
 *
 * Orden recomendado (según el plan): primero hacerla funcionar con SequentialEngine;
 * cambiar a ParallelEngine después es una sola línea.
 */
public class MainGui {

    public static void main(String[] args) {
        // TODO: SwingUtilities.invokeLater(() -> { crear JFrame, GridPanel, controles });
    }
}

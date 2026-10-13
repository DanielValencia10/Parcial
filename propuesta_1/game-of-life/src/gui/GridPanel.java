package gui;

import core.Grid;
import javax.swing.JPanel;

/**
 * Componente que DIBUJA un Grid. Solo pinta, no calcula nada del juego.
 *
 * Pistas:
 *   - extends JPanel y sobrescribir paintComponent(Graphics g).
 *   - Tamaño de celda = min(anchoPanel / cols, altoPanel / rows).
 *   - Para matrices grandes, dibujar líneas de cuadrícula solo si la celda es > ~4 px.
 *   - setGrid(Grid) guarda la referencia y llama repaint().
 *   - (Opcional) MouseListener para alternar el estado de una celda con clic.
 */
public class GridPanel extends JPanel {

    private Grid grid;

    public void setGrid(Grid grid) {
        // TODO: guardar y repintar
    }

    // TODO: protected void paintComponent(java.awt.Graphics g)
}

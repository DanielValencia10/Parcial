"""
renderer.py — Convierte la matriz en una imagen de pygame. [pygame: FUERA DE CLASE]

Dependencias: pygame, numpy [numpy: VISTO EN CLASE: Taller 4].
Solo DIBUJA: no conoce las reglas del juego ni los motores.

POR QUÉ NO UN RECTÁNGULO POR CELDA: dibujar H*W rectángulos por cuadro es muy lento.
Estrategia usada:
  1. Convertir la matriz a un arreglo NumPy (to_array) y mapear 0/1 a dos colores.
  2. Crear una superficie de 1 PÍXEL POR CELDA (matrix_to_surface).
  3. Escalarla con pygame.transform.scale (vecino más cercano; smoothscale se vería borroso).
  4. Dibujar líneas de cuadrícula SOLO si cada celda mide MIN_CELL_PX_FOR_LINES px o más.
"""

import numpy as np
import pygame

COLOR_BG = (18, 18, 22)
COLOR_DEAD = (30, 32, 40)
COLOR_ALIVE = (110, 220, 140)
COLOR_LINES = (48, 50, 60)

MIN_CELL_PX_FOR_LINES = 6

_PALETTE = np.array([COLOR_DEAD, COLOR_ALIVE], dtype=np.uint8)


def to_array(grid):
    """Entrada: matriz del core (lista de listas, filas bytearray o ndarray).
    Salida: ndarray uint8 de forma (filas, columnas)."""
    return np.asarray(grid, dtype=np.uint8)


def matrix_to_surface(arr):
    """Entrada: ndarray (filas, columnas) con 0/1.
    Salida: superficie pygame de 1 píxel por celda (ancho = columnas, alto = filas)."""
    rgb = _PALETTE[(arr > 0).astype(np.intp)]          # (filas, columnas, 3)
    return pygame.surfarray.make_surface(rgb.swapaxes(0, 1))   # surfarray usa (ancho, alto)


def layout(area, rows, cols):
    """Calcula dónde cae el tablero dentro de `area` (pygame.Rect), centrado.

    Salida: (rect_del_tablero, tamaño_de_celda_en_px). El tamaño es entero cuando
    cabe al menos 1 px por celda; si la matriz es más grande que el área, se reduce
    manteniendo la proporción (ya no se distingue celda a celda).
    """
    cell = min(area.w / cols, area.h / rows)
    if cell >= 1:
        cell = int(cell)
        size = (cols * cell, rows * cell)
    else:
        size = (max(1, int(cols * cell)), max(1, int(rows * cell)))
    rect = pygame.Rect(0, 0, *size)
    rect.center = area.center
    return rect, cell


def draw(screen, arr, area, show_grid_lines=True):
    """Dibuja el tablero escalado y centrado en `area`.

    Entradas: screen (Surface), arr (ndarray), area (Rect disponible), show_grid_lines.
    Salida: el Rect donde quedó dibujado el tablero (para mapear el ratón a celdas).
    """
    rows, cols = arr.shape
    rect, cell = layout(area, rows, cols)
    surface = pygame.transform.scale(matrix_to_surface(arr), rect.size)
    screen.blit(surface, rect.topleft)

    if show_grid_lines and cell >= MIN_CELL_PX_FOR_LINES:
        for c in range(cols + 1):
            x = rect.x + c * cell
            pygame.draw.line(screen, COLOR_LINES, (x, rect.y), (x, rect.bottom))
        for r in range(rows + 1):
            y = rect.y + r * cell
            pygame.draw.line(screen, COLOR_LINES, (rect.x, y), (rect.right, y))
    return rect


def cell_from_pos(pos, rect, rows, cols):
    """Convierte una posición de ratón (px) en (fila, columna) de la matriz.

    Entradas: pos (x, y), rect (tablero devuelto por draw), rows y cols de la matriz.
    Salida: (fila, columna), o None si el ratón está fuera del tablero.
    """
    if not rect.collidepoint(pos):
        return None
    c = min(cols - 1, int((pos[0] - rect.x) * cols / rect.w))
    r = min(rows - 1, int((pos[1] - rect.y) * rows / rect.h))
    return r, c

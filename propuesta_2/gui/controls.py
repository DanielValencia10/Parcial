"""
controls.py — Estado de la interfaz, atajos de teclado/ratón y panel de información.

Dependencias: pygame, config. No conoce los motores: solo traduce eventos en
"acciones" (nombre, datos) que app.py ejecuta.

Controles:
  ESPACIO      iniciar / pausar            N          una generación (paso a paso)
  R            aleatorio, semilla fija     S          aleatorio, semilla nueva
  C            limpiar                     1 a 5      versión V1..V5
  ARRIBA/ABAJO trabajadores (hilos/procesos)
  IZQ/DER      velocidad (generaciones/s)  G          mostrar/ocultar cuadrícula
  B / L        blinker / glider bajo el ratón
  clic izq.    pintar celdas viva          clic der.  borrar celdas
  H            mostrar/ocultar ayuda       ESC o Q    salir

Se usan atajos en lugar de botones dibujados: menos código y suficiente para el enunciado.
"""

from dataclasses import dataclass

import pygame

import config
from core.registry import ETIQUETAS

HUD_HEIGHT = 112

# Gen/s objetivo. 0 = sin límite (lo más rápido que permita el motor).
SPEEDS = [1, 2, 5, 10, 20, 30, 60, 0]

VERSION_LABELS = ETIQUETAS

_HELP_LINES = [
    "ESPACIO: iniciar/pausar   N: paso   R: aleatorio (semilla fija)   S: semilla nueva   C: limpiar",
    "1-5: version (5 = MPI)   Arriba/Abajo: trabajadores   Izq/Der: velocidad   G: cuadricula   B/L: blinker/glider",
    "Clic izq.: pintar   Clic der.: borrar   H: ocultar ayuda   Esc: salir",
]

_COLOR_TEXT = (220, 222, 230)
_COLOR_DIM = (140, 144, 158)
_COLOR_ACCENT = (110, 220, 140)
_COLOR_WARN = (240, 180, 90)
_COLOR_PANEL = (26, 27, 34)


@dataclass
class UIState:
    """Estado mutable de la interfaz."""
    running: bool = False
    version: int = 1
    workers_idx: int = 0
    speed_idx: int = 3
    show_lines: bool = True
    show_help: bool = True
    generation: int = 0
    alive: int = 0
    ms_per_gen: float = 0.0
    seed: int = config.SEMILLA
    status: str = ""
    painting: int = None     # None = no se está pintando; 1 = pintando vivas; 0 = borrando

    @property
    def workers(self):
        return config.TRABAJADORES[self.workers_idx]

    @property
    def fps(self):
        return SPEEDS[self.speed_idx]


def handle_event(event, state, cell_at):
    """Procesa un evento de pygame.

    Entradas: event; state (UIState, se puede modificar); cell_at(pos) -> (fila, col) | None.
    Salida: una acción (nombre, datos) para que app.py la ejecute, o None.
    Acciones: quit, step, random_fixed, random_new, clear, version, workers, paint, pattern.
    """
    if event.type == pygame.QUIT:
        return ("quit", None)

    if event.type == pygame.KEYDOWN:
        k = event.key
        if k in (pygame.K_ESCAPE, pygame.K_q):
            return ("quit", None)
        if k == pygame.K_SPACE:
            state.running = not state.running
            state.status = ""
        elif k == pygame.K_n:
            state.running = False
            return ("step", None)
        elif k == pygame.K_r:
            return ("random_fixed", None)
        elif k == pygame.K_s:
            return ("random_new", None)
        elif k == pygame.K_c:
            return ("clear", None)
        elif k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
            return ("version", k - pygame.K_0)
        elif k == pygame.K_UP:
            return ("workers", +1)
        elif k == pygame.K_DOWN:
            return ("workers", -1)
        elif k == pygame.K_RIGHT:
            state.speed_idx = min(len(SPEEDS) - 1, state.speed_idx + 1)
        elif k == pygame.K_LEFT:
            state.speed_idx = max(0, state.speed_idx - 1)
        elif k == pygame.K_g:
            state.show_lines = not state.show_lines
        elif k == pygame.K_h:
            state.show_help = not state.show_help
        elif k in (pygame.K_b, pygame.K_l):
            cell = cell_at(pygame.mouse.get_pos())
            if cell is not None:
                return ("pattern", ("blinker" if k == pygame.K_b else "glider", *cell))

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
        state.painting = 1 if event.button == 1 else 0
        cell = cell_at(event.pos)
        if cell is not None:
            return ("paint", (*cell, state.painting))

    elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
        state.painting = None

    elif event.type == pygame.MOUSEMOTION and state.painting is not None:
        cell = cell_at(event.pos)
        if cell is not None:
            return ("paint", (*cell, state.painting))

    return None


def draw_hud(screen, state, font, grid_shape):
    """Dibuja el panel inferior con el estado y la ayuda.

    Entradas: screen, state (UIState), font, grid_shape (filas, columnas) o None.
    """
    w, h = screen.get_size()
    panel = pygame.Rect(0, h - HUD_HEIGHT, w, HUD_HEIGHT)
    pygame.draw.rect(screen, _COLOR_PANEL, panel)

    line_h = font.get_linesize() + 2
    x, y = 12, panel.y + 8

    estado = "EJECUTANDO" if state.running else "PAUSA"
    workers = str(state.workers) if state.version != 1 else "-"
    fps = "max" if state.fps == 0 else str(state.fps)
    size = f"{grid_shape[0]}x{grid_shape[1]}" if grid_shape else "-"

    _text(screen, font, estado, x, y, _COLOR_ACCENT if state.running else _COLOR_WARN)
    _text(screen, font,
          f"V{state.version} ({VERSION_LABELS[state.version]})   trabajadores: {workers}"
          f"   generacion: {state.generation}   vivas: {state.alive}",
          x + 130, y, _COLOR_TEXT)
    y += line_h
    ms = f"{state.ms_per_gen:.2f}" if state.ms_per_gen else "-"
    _text(screen, font,
          f"ms/generacion: {ms}   velocidad: {fps} gen/s   matriz: {size}   semilla: {state.seed}",
          x, y, _COLOR_TEXT)
    y += line_h

    if state.show_help:
        for line in _HELP_LINES:
            _text(screen, font, line, x, y, _COLOR_DIM)
            y += line_h
    if state.status:
        _text(screen, font, state.status, x, panel.bottom - line_h - 2, _COLOR_WARN)


def _text(screen, font, text, x, y, color):
    screen.blit(font.render(text, True, color), (x, y))

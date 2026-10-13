"""
app.py — Punto de entrada de la GUI (pygame). [FUERA DE CLASE: exigido por el enunciado]

Ejecutar desde la raíz del proyecto:  python -m gui.app

Dependencias: core.* (SOLO lo usa; NUNCA lo modifica), renderer, controls, config.
Nadie importa gui desde benchmark o tests: dibujar contamina los tiempos.

Qué usa del core (nada más):
  - core.grid.new_grid / randomize           -> crear y llenar la matriz
  - core.patterns.place_blinker / place_glider -> botones B y L
  - el contrato core.engine_base.Engine: Engine(grid, workers), step(), snapshot(), close()

REGLAS:
  - pygame vive SOLO en el proceso principal; los procesos de V3 no tocan la GUI.
  - Bucle: leer eventos -> (si está corriendo) engine.step() -> dibujar -> limitar FPS.
  - Cambiar versión o trabajadores = cerrar el motor y crear otro con la matriz actual.
  - Pintar celdas edita la matriz y reconstruye el motor la próxima vez que se avance
    (así no se crea un pool de procesos por cada clic).
  - Si una pieza del core aún no está implementada (NotImplementedError) o una versión
    no existe todavía, la GUI NO se cae: pausa y lo muestra en el panel inferior.
  - Matriz moderada (config.GUI_TAMANO): la GUI no sirve para medir rendimiento.

Con V2/V3 y una matriz pequeña la GUI puede ir MÁS lenta que con V1: es normal
(overhead de sincronización / comunicación) y es un buen ejemplo para la sustentación.
"""

import os
import random
import time
import traceback

import pygame

import config
from core import grid as grid_mod
from core import patterns
from core.registry import EngineUnavailable, load_engine_class, version_de_modo
from gui import controls, renderer

# Las versiones (V1..V5) se listan en core/registry.py y se importan bajo demanda:
# si falta una (p. ej. mpi4py para V5), el resto funciona.

WINDOW_SIZE = (900, 760)


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Juego de la Vida paralelo")
        self.screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        self.font = pygame.font.SysFont("consolas,dejavusansmono,couriernew", 15)
        self.clock = pygame.time.Clock()
        # arranca con la versión que elige config.MODO_PARALELO y GUI_TRABAJADORES trabajadores
        self.ui = controls.UIState(version=version_de_modo(config.MODO_PARALELO),
                                   workers_idx=config.TRABAJADORES.index(config.GUI_TRABAJADORES))

        self.grid = None            # última matriz conocida (la que se dibuja / se edita)
        self.arr = None             # esa misma matriz como ndarray (para dibujar y contar)
        self.engine = None          # motor actual; None => hay que (re)crearlo
        self.board_rect = pygame.Rect(0, 0, 1, 1)
        self.running_app = True

        self._safe(self._new_grid, randomize=True, seed=self.ui.seed)

    # ------------------------------------------------------------------ utilidades
    def _safe(self, fn, *args, **kwargs):
        """Ejecuta fn; si el core aún no está implementado, pausa y avisa en el panel."""
        try:
            return fn(*args, **kwargs)
        except NotImplementedError as exc:
            # el último frame del traceback es la función del core que lanzó el error
            origin = traceback.extract_tb(exc.__traceback__)[-1]
            self.ui.running = False
            self.ui.status = (f"Pendiente de implementar: {origin.name}() "
                              f"en {os.path.basename(origin.filename)}")
        except EngineUnavailable as exc:
            self.ui.running = False
            self.ui.status = str(exc)
        return None

    def _cell_at(self, pos):
        if self.arr is None:
            return None
        return renderer.cell_from_pos(pos, self.board_rect, *self.arr.shape)

    def _set_grid(self, grid):
        self.grid = grid
        self.arr = renderer.to_array(grid)
        self.ui.alive = int(self.arr.sum())

    def _close_engine(self):
        if self.engine is not None:
            self.engine.close()
            self.engine = None

    # ------------------------------------------------------------------ acciones
    def _new_grid(self, randomize, seed=None):
        size = config.GUI_TAMANO
        g = grid_mod.new_grid(size, size)
        if randomize:
            self.ui.seed = seed
            grid_mod.randomize(g, seed, config.DENSIDAD)
        self._close_engine()
        self._set_grid(g)
        self.ui.generation = 0
        self.ui.ms_per_gen = 0.0
        self.ui.status = ""

    def _ensure_engine(self):
        if self.engine is None:
            cls = load_engine_class(self.ui.version)
            self.engine = cls(self.grid, self.ui.workers)

    def _switch_version(self, version):
        """Cambia de versión; si no se puede cargar, se queda con la anterior."""
        previous = self.ui.version
        self.ui.version = version
        self.ui.status = ""
        self._close_engine()
        try:
            self._ensure_engine()       # falla pronto si la versión no existe
        except EngineUnavailable:
            self.ui.version = previous
            raise

    def _step_once(self):
        self._ensure_engine()
        t0 = time.perf_counter()
        self.engine.step()
        dt_ms = (time.perf_counter() - t0) * 1000
        self._set_grid(self.engine.snapshot())
        self.ui.generation += 1
        # promedio exponencial: estable y sin guardar historial
        prev = self.ui.ms_per_gen
        self.ui.ms_per_gen = dt_ms if prev == 0 else 0.9 * prev + 0.1 * dt_ms

    def _paint(self, r, c, value):
        if self.grid is None:
            return
        self.grid[r][c] = value       # el snapshot es una copia (contrato de Engine)
        self.arr[r, c] = value
        self.ui.alive = int(self.arr.sum())
        self._close_engine()          # se recrea con la matriz editada al avanzar

    def _place_pattern(self, kind, r, c):
        if self.grid is None:
            return
        place = patterns.place_blinker if kind == "blinker" else patterns.place_glider
        place(self.grid, r, c)
        self._set_grid(self.grid)
        self._close_engine()

    def _apply(self, action):
        name, data = action
        if name == "quit":
            self.running_app = False
        elif name == "step":
            self._safe(self._step_once)
        elif name == "random_fixed":
            self.ui.running = False
            self._safe(self._new_grid, randomize=True, seed=config.SEMILLA)
        elif name == "random_new":
            self.ui.running = False
            self._safe(self._new_grid, randomize=True, seed=random.randrange(10**6))
        elif name == "clear":
            self.ui.running = False
            self._safe(self._new_grid, randomize=False)
        elif name == "version":
            if data != self.ui.version:
                self._safe(self._switch_version, data)
        elif name == "workers":
            n = len(config.TRABAJADORES)
            self.ui.workers_idx = (self.ui.workers_idx + data) % n
            self._close_engine()
        elif name == "paint":
            self._paint(*data)
        elif name == "pattern":
            self._safe(self._place_pattern, *data)

    # ------------------------------------------------------------------ bucle
    def _draw(self):
        self.screen.fill(renderer.COLOR_BG)
        w, h = self.screen.get_size()
        area = pygame.Rect(0, 0, w, h - controls.HUD_HEIGHT)
        if self.arr is not None:
            self.board_rect = renderer.draw(self.screen, self.arr, area, self.ui.show_lines)
            shape = self.arr.shape
        else:
            msg = "Matriz no disponible: implementar core/grid.py (new_grid, randomize)"
            surf = self.font.render(msg, True, (240, 180, 90))
            self.screen.blit(surf, surf.get_rect(center=area.center))
            self.board_rect = pygame.Rect(0, 0, 1, 1)
            shape = None
        controls.draw_hud(self.screen, self.ui, self.font, shape)
        pygame.display.flip()

    def run(self):
        try:
            while self.running_app:
                for event in pygame.event.get():
                    action = controls.handle_event(event, self.ui, self._cell_at)
                    if action:
                        self._apply(action)
                if self.ui.running:
                    self._safe(self._step_once)
                self._draw()
                self.clock.tick(self.ui.fps)
        finally:
            self._close_engine()
            pygame.quit()


def main():
    """Inicializa pygame y ejecuta el bucle principal."""
    App().run()


if __name__ == "__main__":
    main()

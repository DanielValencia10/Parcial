"""
engine_base.py — Contrato común de todas las versiones (V1..V4).

Dependencias: grid.
Lo usan: v1..v4 (lo implementan); gui, benchmark y tests (dependen SOLO de este contrato,
no de la clase concreta; así se cambia de versión sin tocar nada más).

CICLO DE VIDA (importante para el benchmark):
  1. __init__  : crea hilos / pool de procesos UNA vez (costo de arranque, se mide APARTE).
  2. run(n)    : avanza n generaciones (esto es lo único que el benchmark cronometra).
  3. close()   : libera hilos / procesos.
  Error común: crear y destruir hilos/pool en cada generación.
"""


class Engine:
    """Interfaz base. Cada versión hereda y rellena los métodos."""

    name = "base"   # Etiqueta para el CSV y las gráficas: "v1", "v2", "v3", "v4"

    def __init__(self, initial_grid, workers=1):
        """Prepara el motor a partir de una COPIA de initial_grid (no modifica el original).

        Entradas: initial_grid, workers (hilos o procesos; V1 lo ignora).
        """
        raise NotImplementedError

    def run(self, generations):
        """Avanza `generations` generaciones.

        Para la GUI se usa run(1) (o step()); para el benchmark, run(G) completo.
        """
        raise NotImplementedError

    def step(self):
        """Avanza una generación (equivale a run(1))."""
        raise NotImplementedError

    def snapshot(self):
        """Devuelve (una copia de) la matriz actual, para dibujar o comparar."""
        raise NotImplementedError

    def close(self):
        """Libera hilos/procesos. Debe poder llamarse más de una vez sin error."""
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()          # se llama siempre, incluso si hubo una excepción
        return False          # no se traga la excepción

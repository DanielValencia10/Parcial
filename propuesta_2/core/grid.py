"""
grid.py — Representación de la matriz y utilidades básicas.

Dependencias: config.
Lo usan: rules, partition, patterns, todas las versiones, GUI, benchmark y tests.
NO debe importar ninguna versión (V1..V4) ni la GUI.

DECISIÓN DE REPRESENTACIÓN (acordar en grupo y documentar):
  - V1/V2/V3 en Python puro: lista de listas de enteros (0/1) o lista de bytearray,
    una por fila. Una fila = un objeto contiguo, fácil de enviar entre procesos.
  - V4 y GUI usan arreglos NumPy [VISTO EN CLASE: Taller 4].
  Decidan si usan UN formato en todo el core (más simple) o convierten en los bordes.

Orden por filas (row-major): una banda de filas es memoria contigua => buena
localidad de caché [VISTO EN CLASE: Sesión Paralelismo, localidad y caché].

DECISIÓN TOMADA: lista de bytearray (una por fila, valores 0/1) en TODO el core.
  - bytearray es mutable (la GUI pinta con grid[r][c] = v) y compacto (1 byte por celda).
  - np.asarray(grid, dtype=np.uint8) la convierte sin problema (renderer.to_array).
  - Una fila es un objeto contiguo: se envía barata a otro proceso (V3) o por MPI (V5).
"""

import hashlib
import random


def new_grid(h, w):
    """Crea una matriz h x w con todas las celdas muertas.

    Entradas: h (filas), w (columnas).
    Salida: matriz nueva en el formato elegido.
    """
    return [bytearray(w) for _ in range(h)]


def randomize(grid, seed, density):
    """Llena la matriz con celdas vivas al azar, de forma reproducible.

    Entradas: grid (se modifica), seed (entero fijo), density (0..1).
    Salida: la misma matriz.
    Importante: con la misma semilla, TODAS las versiones deben partir del mismo estado.
    Pista: random.Random(seed) propio, no el generador global.
    """
    rng = random.Random(seed)          # generador propio: no toca el global
    for fila in grid:
        for c in range(len(fila)):
            fila[c] = 1 if rng.random() < density else 0
    return grid


def copy(grid):
    """Copia profunda de la matriz (los tests parten de copias del mismo estado)."""
    return [bytearray(fila) for fila in grid]


def equals(a, b):
    """True si ambas matrices son idénticas celda a celda (comparación directa)."""
    if len(a) != len(b):
        return False
    for fila_a, fila_b in zip(a, b):
        if fila_a != fila_b:       # bytearray == bytearray compara el contenido
            return False
    return True


def signature(grid):
    """Devuelve un hash/resumen del contenido para comparar matrices grandes rápido."""
    h = hashlib.sha256()
    for fila in grid:
        h.update(bytes(fila))
    return h.hexdigest()


def alive_count(grid):
    """Número de celdas vivas.

    Ojo: es una REDUCCIÓN (trampa serial). Si se hace en paralelo, calcular
    parciales por trabajador y sumarlos al final, en vez de usar un Lock compartido.
    """
    total = 0
    for fila in grid:
        total += sum(fila)         # sum sobre bytearray suma los 0/1
    return total

"""
Lee results/tiempos.csv y genera las gráficas del informe.

Dependencias: pandas y matplotlib   (pip install pandas matplotlib)

Formato esperado del CSV (lo escribe benchmark.Benchmark):
    motor,tamano,hilos,generaciones,repeticion,tiempo_ms

PASOS:
  1. Leer el CSV con pandas.
  2. Agrupar por (motor, tamano, hilos) y calcular la MEDIANA (o el promedio) de tiempo_ms
     sobre las repeticiones.
  3. Tiempo secuencial T_seq por tamaño = mediana de las filas con motor == "sequential".
  4. Speedup    S(p) = T_seq / T_paralelo(p)
     Eficiencia E(p) = S(p) / p

GRÁFICAS (guardar como PNG en plots/):
  a) tiempo_vs_tamano.png
       Eje X: tamaño de la matriz. Eje Y: tiempo (ms). Una curva por número de hilos
       (incluir la secuencial). Considerar escala logarítmica si el rango es grande.
  b) speedup_vs_hilos.png
       Eje X: hilos. Eje Y: speedup. Una curva por tamaño de matriz
       + la LÍNEA IDEAL (S = p) como referencia punteada.
  c) (opcional) eficiencia_vs_hilos.png
       Misma idea con E(p); la ideal es 1.0.

Qué buscar al interpretar (para el informe):
  - 100x100 probablemente NO mejora (o empeora): el overhead de hilos/barreras domina.
  - A tamaños grandes el speedup se acerca a lo ideal... hasta que choca con la
    Ley de Amdahl, el ancho de banda de memoria o los núcleos físicos (vs lógicos).
"""

import sys
from pathlib import Path

# import pandas as pd
# import matplotlib.pyplot as plt

CSV_PATH = Path(__file__).parent.parent / "results" / "tiempos.csv"
OUT_DIR = Path(__file__).parent


def load_data():
    # TODO: pd.read_csv(CSV_PATH)
    raise NotImplementedError


def compute_metrics(df):
    # TODO: agrupar, mediana, T_seq por tamaño, speedup y eficiencia
    raise NotImplementedError


def plot_time_vs_size(metrics):
    # TODO
    raise NotImplementedError


def plot_speedup_vs_threads(metrics):
    # TODO
    raise NotImplementedError


def main():
    # TODO: orquestar las funciones anteriores
    print("Pendiente de implementar", file=sys.stderr)


if __name__ == "__main__":
    main()

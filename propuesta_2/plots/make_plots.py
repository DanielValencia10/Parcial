"""
make_plots.py — Lee results/tiempos.csv y genera las gráficas del informe.

Ejecutar desde la raíz:  python -m plots.make_plots
Dependencias: matplotlib [FUERA DE CLASE; ya se usó en el Taller 4].
Se lee el CSV con el módulo estándar `csv` y medianas con `statistics.median`
(sin pandas: es innecesario y no se vio en clase).

PASOS:
  1. Leer el CSV.
  2. Agrupar por (version, tamano, trabajadores) y calcular la MEDIANA de tiempo_computo_s.
  3. T_V1 por tamaño = mediana de las filas de V1.
  4. Speedup    S(p) = T_V1 / T_par(p)
     Eficiencia E(p) = S(p) / p
  5. Estimar la fracción serial (Amdahl) a partir de S(p):
        f ≈ (1/S - 1/p) / (1 - 1/p)       [VISTO EN CLASE: Ley de Amdahl]

BASE DEL SPEEDUP:
  - V2, V3, V5 -> contra V1 (Python puro secuencial).
  - V4 -> contra V4 con 1 hilo (secuencial VECTORIZADA). Compararla con V1 mezclaría el efecto
    de la vectorización (SIMD) con el del paralelismo. Aun así se reporta su factor contra V1
    por separado en results/resumen.md (columna "vs V1").

SALIDAS (results/figures/ y results/resumen.md):
  tiempo_vs_tamano.png          X = tamaño, Y = tiempo; una curva por nº de trabajadores, un panel por versión
  tiempo_vs_trabajadores.png    X = trabajadores, Y = tiempo; un panel por tamaño
  speedup_vs_trabajadores.png   X = trabajadores, Y = speedup vs V1 (V2, V3, V5) + línea ideal S = p
  speedup_v4_vs_v4_1hilo.png    speedup de V4 contra su propia base
  eficiencia_vs_trabajadores.png
"""

import csv
import os
import statistics

import matplotlib

matplotlib.use("Agg")               # guardar PNG sin abrir ventana
import matplotlib.pyplot as plt     # noqa: E402
import matplotlib.ticker            # noqa: E402,F401

RUTA_CSV = os.path.join("results", "tiempos.csv")
CARPETA_FIG = os.path.join("results", "figures")
RUTA_RESUMEN = os.path.join("results", "resumen.md")

NOMBRES = {
    "v1": "V1 secuencial",
    "v2": "V2 hilos + Barrier",
    "v3": "V3 procesos + fantasmas",
    "v4": "V4 hilos + NumPy",
    "v5": "V5 MPI",
}
COLORES = {"v1": "#7f8c8d", "v2": "#e67e22", "v3": "#3498db", "v4": "#9b59b6", "v5": "#2ecc71"}
PARALELAS_VS_V1 = ["v2", "v3", "v5"]


def load_rows(csv_path):
    """Lee el CSV y devuelve una lista de filas (diccionarios con tipos numéricos)."""
    filas = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            filas.append({
                "version": fila["version"],
                "tamano": int(fila["tamano"]),
                "trabajadores": int(fila["trabajadores"]),
                "generaciones": int(fila["generaciones"]),
                "repeticion": int(fila["repeticion"]),
                "tiempo_setup_s": float(fila["tiempo_setup_s"]),
                "tiempo_computo_s": float(fila["tiempo_computo_s"]),
            })
    return filas


def compute_metrics(rows):
    """Calcula medianas, speedup, eficiencia y fracción serial estimada por configuración.

    Devuelve una lista de diccionarios (uno por version/tamano/trabajadores).
    """
    grupos = {}
    for fila in rows:
        clave = (fila["version"], fila["tamano"], fila["trabajadores"])
        grupos.setdefault(clave, []).append(fila)

    mediana = {c: statistics.median(f["tiempo_computo_s"] for f in filas) for c, filas in grupos.items()}
    setup = {c: statistics.median(f["tiempo_setup_s"] for f in filas) for c, filas in grupos.items()}

    metricas = []
    for (version, tamano, p), t in sorted(mediana.items()):
        t_v1 = mediana.get(("v1", tamano, 1))
        t_v4_1 = mediana.get(("v4", tamano, 1))
        base = t_v4_1 if version == "v4" else t_v1          # V4 usa su propia base
        speedup = base / t if base else None
        eficiencia = speedup / p if speedup is not None else None
        if speedup is not None and p > 1:
            f_serial = (1 / speedup - 1 / p) / (1 - 1 / p)  # Amdahl despejando f
        else:
            f_serial = None
        metricas.append({
            "version": version, "tamano": tamano, "trabajadores": p,
            "tiempo_s": t, "setup_s": setup[(version, tamano, p)],
            "speedup": speedup, "eficiencia": eficiencia, "fraccion_serial": f_serial,
            "vs_v1": (t_v1 / t) if t_v1 else None,
            "generaciones": grupos[(version, tamano, p)][0]["generaciones"],
            "repeticiones": len(grupos[(version, tamano, p)]),
        })
    return metricas


# ---------------------------------------------------------------- utilidades de dibujo
def _versiones(metricas):
    return sorted({m["version"] for m in metricas})


def _tamanos(metricas):
    return sorted({m["tamano"] for m in metricas})


def _trabajadores(metricas, version):
    return sorted({m["trabajadores"] for m in metricas if m["version"] == version})


def _serie(metricas, version, **filtros):
    """Filas de `version` que cumplen los filtros, ordenadas por tamaño y trabajadores."""
    return sorted((m for m in metricas if m["version"] == version
                   and all(m[k] == v for k, v in filtros.items())),
                  key=lambda m: (m["tamano"], m["trabajadores"]))


def _guardar(fig, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print("guardado", out_path)


# ---------------------------------------------------------------- gráficas
def plot_time_vs_size(metrics, out_path):
    """Gráfica de tiempo vs tamaño: un panel por versión paralela, una curva por nº de trabajadores."""
    versiones = [v for v in _versiones(metrics) if v != "v1"]
    fig, ejes = plt.subplots(1, len(versiones), figsize=(4.6 * len(versiones), 4.2), squeeze=False)
    v1 = _serie(metrics, "v1", trabajadores=1)
    for eje, version in zip(ejes[0], versiones):
        for p in _trabajadores(metrics, version):
            serie = _serie(metrics, version, trabajadores=p)
            eje.plot([m["tamano"] for m in serie], [m["tiempo_s"] for m in serie],
                     marker="o", label=f"p = {p}")
        eje.plot([m["tamano"] for m in v1], [m["tiempo_s"] for m in v1],
                 "k--", marker="s", label="V1 (base)")
        eje.set_xscale("log")
        eje.set_yscale("log")
        eje.set_xticks(_tamanos(metrics))
        eje.set_xticklabels([f"{t}²" for t in _tamanos(metrics)])
        eje.set_xlabel("Tamaño de la matriz")
        eje.set_ylabel("Tiempo de ejecución (s)")
        eje.set_title(NOMBRES[version])
        eje.grid(True, which="both", alpha=0.3)
        eje.legend(fontsize=8)
    generaciones = metrics[0]["generaciones"]
    fig.suptitle(f"Tiempo vs tamaño de la matriz ({generaciones} generaciones, mediana)")
    _guardar(fig, out_path)


def plot_time_vs_workers(metrics, out_path):
    """Tiempo vs número de trabajadores: un panel por tamaño, una curva por versión."""
    tamanos = _tamanos(metrics)
    fig, ejes = plt.subplots(1, len(tamanos), figsize=(4.6 * len(tamanos), 4.2), squeeze=False)
    for eje, tamano in zip(ejes[0], tamanos):
        v1 = _serie(metrics, "v1", tamano=tamano, trabajadores=1)
        if v1:
            eje.axhline(v1[0]["tiempo_s"], color=COLORES["v1"], linestyle="--", label="V1 (base)")
        for version in _versiones(metrics):
            if version == "v1":
                continue
            serie = _serie(metrics, version, tamano=tamano)
            eje.plot([m["trabajadores"] for m in serie], [m["tiempo_s"] for m in serie],
                     marker="o", color=COLORES[version], label=NOMBRES[version])
        eje.set_xscale("log", base=2)
        eje.set_yscale("log")
        eje.set_xticks(sorted({m["trabajadores"] for m in metrics}))
        eje.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        eje.set_xlabel("Hilos / procesos")
        eje.set_ylabel("Tiempo de ejecución (s)")
        eje.set_title(f"Matriz {tamano}x{tamano}")
        eje.grid(True, which="both", alpha=0.3)
        eje.legend(fontsize=8)
    _guardar(fig, out_path)


def plot_speedup_vs_workers(metrics, out_path):
    """Gráfica de speedup (contra V1) vs trabajadores con la línea ideal S = p."""
    tamanos = _tamanos(metrics)
    todos_p = sorted({m["trabajadores"] for m in metrics})
    fig, ejes = plt.subplots(1, len(tamanos), figsize=(4.6 * len(tamanos), 4.2), squeeze=False)
    for eje, tamano in zip(ejes[0], tamanos):
        eje.plot(todos_p, todos_p, "k:", label="ideal S = p")
        eje.axhline(1.0, color="#bbbbbb", linewidth=0.8)
        for version in PARALELAS_VS_V1:
            serie = _serie(metrics, version, tamano=tamano)
            if serie:
                eje.plot([m["trabajadores"] for m in serie], [m["speedup"] for m in serie],
                         marker="o", color=COLORES[version], label=NOMBRES[version])
        eje.set_xscale("log", base=2)
        eje.set_xticks(todos_p)
        eje.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        eje.set_xlabel("Hilos / procesos")
        eje.set_ylabel("Speedup = T(V1) / T(p)")
        eje.set_title(f"Matriz {tamano}x{tamano}")
        eje.grid(True, alpha=0.3)
        eje.legend(fontsize=8)
    _guardar(fig, out_path)


def plot_speedup_v4(metrics, out_path):
    """Speedup de V4 contra SU base (V4 con 1 hilo), no contra V1."""
    if not _serie(metrics, "v4"):
        return
    todos_p = _trabajadores(metrics, "v4")
    fig, eje = plt.subplots(figsize=(5.2, 4.4))
    eje.plot(todos_p, todos_p, "k:", label="ideal S = p")
    for tamano in _tamanos(metrics):
        serie = _serie(metrics, "v4", tamano=tamano)
        eje.plot([m["trabajadores"] for m in serie], [m["speedup"] for m in serie],
                 marker="o", label=f"{tamano}x{tamano}")
    eje.set_xscale("log", base=2)
    eje.set_xticks(todos_p)
    eje.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    eje.set_xlabel("Hilos")
    eje.set_ylabel("Speedup = T(V4, 1 hilo) / T(V4, p)")
    eje.set_title("V4 (hilos + NumPy) contra su propia base")
    eje.grid(True, alpha=0.3)
    eje.legend(fontsize=8)
    _guardar(fig, out_path)


def plot_efficiency(metrics, out_path):
    """Eficiencia E = S / p vs trabajadores (un panel por tamaño)."""
    tamanos = _tamanos(metrics)
    todos_p = sorted({m["trabajadores"] for m in metrics})
    fig, ejes = plt.subplots(1, len(tamanos), figsize=(4.6 * len(tamanos), 4.2), squeeze=False)
    for eje, tamano in zip(ejes[0], tamanos):
        eje.axhline(1.0, color="k", linestyle=":", label="ideal E = 1")
        for version in PARALELAS_VS_V1 + ["v4"]:
            serie = _serie(metrics, version, tamano=tamano)
            if serie:
                etiqueta = NOMBRES[version] + (" (base: V4 1 hilo)" if version == "v4" else "")
                eje.plot([m["trabajadores"] for m in serie], [m["eficiencia"] for m in serie],
                         marker="o", color=COLORES[version], label=etiqueta)
        eje.set_xscale("log", base=2)
        eje.set_xticks(todos_p)
        eje.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        eje.set_xlabel("Hilos / procesos")
        eje.set_ylabel("Eficiencia E = S / p")
        eje.set_title(f"Matriz {tamano}x{tamano}")
        eje.grid(True, alpha=0.3)
        eje.legend(fontsize=7)
    _guardar(fig, out_path)


# ---------------------------------------------------------------- tabla para el informe
def write_summary(metrics, out_path):
    """Escribe results/resumen.md con tiempos, speedup, eficiencia y fracción serial."""
    def fmt(valor, decimales=2):
        return "-" if valor is None else f"{valor:.{decimales}f}"

    lineas = ["# Resumen de resultados (medianas)", "",
              "Speedup de V2, V3 y V5 contra V1; el de V4 contra V4 con 1 hilo (columna `vs V1` = contra V1).",
              "`f` = fracción serial estimada con Amdahl, f = (1/S - 1/p) / (1 - 1/p); valores negativos "
              "indican speedup superlineal (efecto de caché/ruido) y no son interpretables.", ""]
    for tamano in _tamanos(metrics):
        generaciones = next(m["generaciones"] for m in metrics if m["tamano"] == tamano)
        lineas += [f"## Matriz {tamano}x{tamano} ({generaciones} generaciones)", "",
                   "| Versión | p | Tiempo (s) | Setup (s) | Speedup | Eficiencia | f | vs V1 |",
                   "|---|---|---|---|---|---|---|---|"]
        for version in _versiones(metrics):
            for m in _serie(metrics, version, tamano=tamano):
                lineas.append(f"| {NOMBRES[version]} | {m['trabajadores']} | {fmt(m['tiempo_s'], 3)} | "
                              f"{fmt(m['setup_s'], 3)} | {fmt(m['speedup'])} | {fmt(m['eficiencia'])} | "
                              f"{fmt(m['fraccion_serial'])} | {fmt(m['vs_v1'])} |")
        lineas.append("")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    print("guardado", out_path)


def main():
    """Orquesta la lectura, el cálculo y la generación de las figuras."""
    filas = load_rows(RUTA_CSV)
    if not filas:
        raise SystemExit(f"{RUTA_CSV} está vacío: ejecutar primero python -m benchmark.run_benchmark")
    metricas = compute_metrics(filas)
    plot_time_vs_size(metricas, os.path.join(CARPETA_FIG, "tiempo_vs_tamano.png"))
    plot_time_vs_workers(metricas, os.path.join(CARPETA_FIG, "tiempo_vs_trabajadores.png"))
    plot_speedup_vs_workers(metricas, os.path.join(CARPETA_FIG, "speedup_vs_trabajadores.png"))
    plot_speedup_v4(metricas, os.path.join(CARPETA_FIG, "speedup_v4_vs_v4_1hilo.png"))
    plot_efficiency(metricas, os.path.join(CARPETA_FIG, "eficiencia_vs_trabajadores.png"))
    write_summary(metricas, RUTA_RESUMEN)


if __name__ == "__main__":
    main()

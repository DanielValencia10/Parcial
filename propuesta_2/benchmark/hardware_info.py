"""
hardware_info.py — Registra el hardware y el entorno de las pruebas en results/hardware.txt.

Datos a registrar: modelo de CPU, núcleos FÍSICOS y LÓGICOS, RAM, sistema operativo,
versión de Python, plan de energía. Los núcleos físicos vs lógicos son clave para
interpretar por qué el speedup se estanca (p. ej. 4 físicos / 8 lógicos).

Ejecutar desde la raíz:  python -m benchmark.hardware_info
En Windows el modelo y los núcleos se obtienen con `Get-CimInstance Win32_Processor`.
"""

import os
import platform
import subprocess
import sys

RUTA_POR_DEFECTO = os.path.join("results", "hardware.txt")


def _powershell(comando):
    """Ejecuta un comando de PowerShell y devuelve su salida como texto ('' si falla)."""
    try:
        salida = subprocess.run(["powershell", "-NoProfile", "-Command", comando],
                                capture_output=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return ""
    for codificacion in ("utf-8", "cp850"):
        try:
            return salida.decode(codificacion).strip()
        except UnicodeDecodeError:
            continue
    return salida.decode("utf-8", errors="replace").strip()


def _version(paquete):
    try:
        modulo = __import__(paquete)
        return getattr(modulo, "__version__", None) or getattr(getattr(modulo, "version", None), "ver", "?")
    except ImportError:
        return "no instalado"


def collect():
    """Devuelve un diccionario con los datos de hardware y entorno."""
    datos = {"Núcleos lógicos": str(os.cpu_count())}
    if platform.system() == "Windows":
        cpu = _powershell("Get-CimInstance Win32_Processor | Select-Object -First 1 "
                          "-ExpandProperty Name")
        fisicos = _powershell("(Get-CimInstance Win32_Processor | "
                              "Measure-Object NumberOfCores -Sum).Sum")
        ram = _powershell("[math]::Round((Get-CimInstance Win32_ComputerSystem)"
                          ".TotalPhysicalMemory / 1GB, 1)")
        plan = _powershell("powercfg /getactivescheme")
        datos["CPU"] = cpu or platform.processor()
        datos["Núcleos físicos"] = fisicos or "?"
        datos["RAM"] = f"{ram} GB" if ram else "?"
        datos["Plan de energía"] = plan or "?"
    else:
        datos["CPU"] = platform.processor() or platform.machine()
        datos["Núcleos físicos"] = "?"
        datos["RAM"] = "?"
        datos["Plan de energía"] = "?"
    datos["Sistema operativo"] = platform.platform()
    gil = getattr(sys, "_is_gil_enabled", lambda: True)()
    datos["Versión de Python"] = f"{platform.python_version()} ({'con GIL' if gil else 'SIN GIL'})"
    datos["numpy"] = _version("numpy")
    datos["mpi4py"] = _version("mpi4py")
    datos["matplotlib"] = _version("matplotlib")
    return datos


def save(path=RUTA_POR_DEFECTO):
    """Escribe los datos en un archivo de texto legible para anexar al informe."""
    datos = collect()
    carpeta = os.path.dirname(path)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for clave, valor in datos.items():
            f.write(f"{clave}: {valor}\n")
        f.write("Otras aplicaciones abiertas: (anotar a mano; cerrar las pesadas antes de medir)\n")
    return datos


if __name__ == "__main__":
    for clave, valor in save().items():
        print(f"{clave}: {valor}")
    print(f"\nGuardado en {RUTA_POR_DEFECTO}")

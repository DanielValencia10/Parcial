# Hardware de pruebas

> Llenar con la máquina EXACTA donde se corrió el benchmark (la misma para todas las mediciones).

| Dato                         | Valor |
|------------------------------|-------|
| CPU (modelo)                 |       |
| Núcleos físicos              |       |
| Núcleos lógicos (hilos)      |       |
| Frecuencia base / turbo      |       |
| RAM                          |       |
| Sistema operativo            |       |
| Versión de Java (`java -version`) |  |
| Plan de energía / otras apps abiertas |  |

Cómo obtenerlo en Windows (PowerShell):

    Get-CimInstance Win32_Processor | Select Name, NumberOfCores, NumberOfLogicalProcessors

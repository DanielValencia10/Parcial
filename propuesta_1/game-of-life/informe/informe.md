# Game of Life paralelo — Informe

> Cada integrante escribe su parte. Entregar al menos un día antes de la sustentación.

## 1. Introducción y objetivo
<!-- Qué se hizo y para qué. Qué se quiere demostrar (cuándo ayuda el paralelismo). -->

## 2. Descripción del juego y decisiones de diseño
<!-- Reglas de Conway.
     Decisiones justificadas: lenguaje (Java), hilos vs MPI, fronteras (toroidal o muerta),
     división por filas (por qué y no columnas/bloques 2D), almacenamiento plano row-major. -->

## 3. Implementación secuencial
<!-- Doble búfer, función de reglas única compartida (Rules), semilla fija. -->

## 4. Estrategia de paralelización
<!-- EL CENTRO DEL INFORME.
     - Tipo de problema: paralelismo de datos / stencil, descomposición de dominio.
     - Reparto de filas y balance de carga (ej. 1000 filas / 7 hilos).
     - Sincronización: barrera por generación + swap de búferes.
     - Por qué NO hay condiciones de carrera (lecturas de 'actual', escrituras en filas
       disjuntas de 'siguiente').
     - Fronteras entre rangos: lectura directa por memoria compartida.
     - Diagrama del ciclo por generación (opcional pero suma). -->

## 5. Desafíos encontrados y cómo se resolvieron
<!-- - Condiciones de carrera con una sola matriz.
     - Costo de las barreras.
     - Fronteras entre rangos.
     - Balance de carga.
     - Overhead de crear hilos (se crean una vez).
     - Los que les hayan pasado de verdad: son los que más valoran. -->

## 6. Metodología de pruebas
<!-- Hardware: ver informe/hardware.md.
     Tamaños, hilos, generaciones, repeticiones, mediana/promedio, warm-up, misma semilla.
     Verificación de correctitud previa (secuencial == paralelo, blinker, glider). -->

## 7. Resultados y gráficas
<!-- Insertar: plots/tiempo_vs_tamano.png y plots/speedup_vs_hilos.png.
     Tabla con speedup y eficiencia. -->

## 8. Análisis y conclusiones
<!-- - ¿Cuándo ayuda el paralelismo y cuándo no? (100x100 vs 5000x5000)
     - Overhead de hilos/barreras.
     - Ley de Amdahl: fracción secuencial, límite teórico.
     - Núcleos físicos vs lógicos, ancho de banda de memoria.
     - Un resultado "malo" bien explicado es una conclusión válida. -->

## 9. Referencias
<!-- Enunciado, documentación de Java (CyclicBarrier, Thread), Amdahl (1967), etc. -->

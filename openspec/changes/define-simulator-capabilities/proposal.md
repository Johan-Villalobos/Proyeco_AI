# Proposal

## Why

La primera especificación funcional y técnica del simulador debe quedar estructurada como capacidades OpenSpec antes de implementar Django, la matemática de Markov o la interfaz. Esto permite que el motor, los escenarios, las vistas de simulación, el editor de matriz y la visualización tengan requisitos trazables, pruebas y tareas MVT independientes.

## What Changes

- Se introduce la capacidad `markov-engine` para validar matrices estocásticas y calcular distribuciones, trayectorias y estados estacionarios.
- Se introduce la capacidad `scenarios` para persistir escenarios preestablecidos, matrices editadas y el historial de simulaciones.
- Se introduce la capacidad `simulation-views` para exponer las rutas de escenarios, simulación, validación e historial con contratos HTTP consistentes.
- Se introduce la capacidad `matrix-editor` para editar y validar una matriz 4x4 en vivo con retroalimentación visual y restablecimiento.
- Se introduce la capacidad `visualization` para presentar resultados, tiempos, gráficas de barras y evolución de líneas.
- Se incorpora el flujo SDD/OpenSpec completo descrito en la sección 7: propuesta, deltas, validación estricta, aplicación guiada por tareas y archivado.

## Capabilities

### New Capabilities

- `markov-engine`: dominio Python puro para matrices estocásticas, vector inicial, distribuciones por paso, trayectorias y distribución estacionaria.
- `scenarios`: modelos y servicios Django para escenarios base, simulaciones persistidas y historial reciente.
- `simulation-views`: rutas y vistas delgadas para consulta de escenarios, cálculo, validación e historial.
- `matrix-editor`: edición interactiva 4x4, validación cliente, indicador de validez, restablecimiento y antirrebote.
- `visualization`: interfaz Django, tabla de resultados, gráfica de barras y gráfica de líneas en español.

### Modified Capabilities

- Ninguna. El proyecto no contiene capacidades previas.

## Impact

- Afecta `simulator/markov.py`, `simulator/models.py`, `simulator/services.py`, `simulator/views.py`, `simulator/urls.py`, templates y archivos estáticos.
- Afecta las pruebas de dominio, modelos, servicios, API/vistas y templates.
- Introduce los escenarios base "Hora pico mañana", "Día lluvioso" y "Domingo/Festivo", con matrices didácticas no presentadas como datos reales.
- Sigue Django 5.x, SQLite, patrón MVT, Python 3.11+, Chart.js y español colombiano.

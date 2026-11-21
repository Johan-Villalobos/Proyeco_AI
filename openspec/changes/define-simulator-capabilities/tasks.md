# Tasks

## 1. Model

- [x] 1.1 Crear `simulator/markov.py` con `STATES`, `MatrixError` y `validate_matrix`; verificar con pruebas rojas/verdes que rechace forma, valores y suma de filas inválidos y acepte tolerancia 1e-9.
- [x] 1.2 Implementar `initial_vector`, `step`, `distribution_at`, `trajectory` y `stationary` en Python puro; verificar `π(n)`, identidad, absorbente, n=0 y trayectoria 0..10 con `test_markov.py`.
- [x] 1.3 Crear `Scenario` y `Simulation` en `simulator/models.py` con los campos definidos por la sección 4.1; verificar restricciones y persistencia con `test_models.py`.
- [x] 1.4 Implementar `Scenario.clean()` reutilizando `markov.validate_matrix`; verificar matrices válidas e inválidas en `test_models.py`.
- [x] 1.5 Crear la migración de datos `0002_seed_scenarios.py` con Hora pico mañana, Día lluvioso y Domingo/Festivo; verificar con migraciones y `TestCase` que existan exactamente los tres escenarios base.
- [x] 1.6 Implementar `get_scenarios`, `run_simulation`, `save_simulation` y `recent_history` en `simulator/services.py`; verificar orquestación, persistencia e historial máximo de 20 con `test_services.py`.
- [x] 1.7 Documentar dentro del código las equivalencias 1=30 min, 3=1.5 h, 5=2.5 h y 10=5 h; verificar mediante pruebas o revisión del archivo que sean consistentes.

## 2. View

- [x] 2.1 Crear `simulator/urls.py` y rutas para `/`, `/api/scenarios/`, `/api/simulate/`, `/api/validate/` y `/api/history/`; verificar con `django.test.Client` que todas las rutas resuelvan.
- [x] 2.2 Implementar `IndexView` con `Scenario` cargado por el servicio y sin lógica de Markov; verificar con `test_views.py` que la página tenga estado 200 y el contexto esperado.
- [x] 2.3 Implementar `scenarios_api` y `history_api`; verificar códigos 200 y contratos JSON para escenarios e historial máximo.
- [x] 2.4 Implementar `simulate_api` usando servicios para validar y calcular; verificar 200 con `{results, trajectory, interpretation}` y 400 con datos inválidos.
- [x] 2.5 Implementar `validate_api` con `{valid, invalid_rows}`; verificar matriz válida, filas inválidas y respuesta 400.
- [x] 2.6 Aplicar el contrato HTTP uniforme para método no permitido y devolver 405 en métodos incompatibles; verificar todas las rutas con `test_api.py`.
- [x] 2.7 Verificar que los endpoints POST aceptan CSRF desde el template y rechazan solicitudes sin token válido; documentar el comportamiento en la prueba de API.
- [x] 2.8 Mantener las vistas sin cálculo matricial ni HTML construido a mano; verificar mediante revisión del diff y pruebas de API.

## 3. Template

- [x] 3.1 Crear `base.html` con layout, carga de Chart.js y bloque `content`; verificar que la página principal se renderice y contenga los activos necesarios.
- [x] 3.2 Crear `index.html` con selector de escenario, selector de estado, botón Simular y zona de resultados; verificar con `assertContains` los controles principales.
- [x] 3.3 Crear `partials/matrix_editor.html` con 16 inputs numéricos y suma por fila; verificar que existan los 16 campos y las 4 sumas.
- [x] 3.4 Crear `partials/results_table.html` con filas 1, 3, 5 y 10 y columnas Fluido, Moderado, Congestionado y Colapsado; verificar con una respuesta de ejemplo.
- [x] 3.5 Implementar `static/simulator/js/matrix.js` con edición 4x4, validación cliente de 0.001, debounce de 300 ms, indicador verde/rojo y restablecimiento; verificar mediante checklist manual y pruebas disponibles en el entorno.
- [x] 3.6 Implementar `static/simulator/js/api.js` para llamadas fetch, token CSRF, validación y simulación; verificar manualmente 200/400 y ausencia de envío con matriz inválida.
- [x] 3.7 Implementar `static/simulator/js/charts.js` con gráfica de barras y línea; verificar que barras y trayectoria 0..10 se rendericen con Chart.js.
- [x] 3.8 Traducir todos los textos visibles al español y mostrar minutos/horas junto a los pasos; verificar la página manualmente y mediante capturas o revisión.
- [x] 3.9 Incluir el aviso de que las probabilidades son didácticas y no datos reales; verificar que aparezca en la interfaz y el README.
- [x] 3.10 Mantener las plantillas sin reglas de negocio ni consultas ORM; verificar mediante revisión de código y `test_views.py`.

## 4. Integración y calidad

- [ ] 4.1 Escribir o completar las pruebas unitarias de dominio, modelo, servicios, API y vista antes de implementar cada comportamiento; verificar que los casos tengan nombres trazables a los IDs de Scenario.
- [ ] 4.2 Ejecutar `python manage.py test` y corregir fallos antes de continuar; verificar una ejecución completa en verde.
- [ ] 4.3 Ejecutar cobertura y alcanzar al menos 80 % global y 100 % en `markov.py`; verificar con el reporte de `coverage`.
- [ ] 4.4 Ejecutar `openspec validate <change-id> --strict` y corregir los deltas hasta que la validación sea verde.
- [ ] 4.5 Revisar el diff de todas las capas y confirmar que MVT, dominio y servicios respetan las restricciones documentadas; verificar con una revisión final y comandos de prueba verdes.

## Workflow follow-up

- Ejecutar el flujo SDD por fase: commit de spec, commit de pruebas, commit de implementación y PR.
- Archivar el change después de que las tareas estén completas y el proyecto haya sido revisado.

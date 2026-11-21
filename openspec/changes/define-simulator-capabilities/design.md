# Design

## Context

La propuesta establece cinco capacidades nuevas sobre un proyecto Django nuevo. El proyecto seguirá MVT con una capa de dominio puro y una capa de servicios. La persistencia será SQLite y la interfaz usará Chart.js. Los requisitos observables completos están en las cinco especificaciones de este change.

## Goals / Non-Goals

**Goals:**

- Mantener `markov.py` independiente de Django y testeable con Python puro.
- Mantener vistas delgadas mediante `services.py`.
- Persistir escenarios y simulaciones sin mezclar cálculos en modelos.
- Mantener plantillas libres de lógica de negocio y consultas.
- Hacer trazables las capacidades con pruebas e IDs de Scenario.
- Validar una matriz en servidor y ofrecer retroalimentación inmediata en el cliente.

**Non-Goals:**

- Datos reales o calibración de tráfico vial.
- Sustituir Django ORM por otro motor de persistencia.
- Incorporar autenticación, autorización o cuentas de usuario.
- Implementar análisis predictivo distinto de una cadena de Markov discreta.
- Crear estaciones geográficas, rutas adicionales o gestión avanzada de historial.

## Decisions

### Motor de dominio Python puro

Se implementará `simulator/markov.py` con listas de Python y operaciones locales. Se evitará importar Django para que las pruebas y cálculos puedan ejecutarse en aislamiento.

`validate_matrix` será la única fuente de reglas sobre forma, intervalo y suma de filas, con tolerancia 1e-9. Las operaciones `initial_vector`, `step`, `distribution_at`, `trajectory` y `stationary` operarán sobre estructuras simples.

Alternativas consideradas: NumPy reduciría código numérico, pero añade una dependencia innecesaria para una matriz 4x4 y dificultaría el proyecto mínimo.

### Modelos y migraciones

`Scenario` almacenará nombre, slug, descripción, matriz y condición de escenario preestablecido. `Simulation` almacenará estado inicial, matriz usada, resultados y fecha.

La restricción de matriz se repetirá en `Scenario.clean()` llamando a `markov.validate_matrix`, evitando que la regla viva solo en la vista.

Alternativas consideradas: validar exclusivamente en API no protege la integridad por ORM/admin. Los cálculos no se almacenarán como métodos del modelo.

### Servicios entre dominio y persistencia

`get_scenarios`, `run_simulation`, `save_simulation` y `recent_history` se ubicarán en `simulator/services.py`. Las vistas usarán estos servicios y no calcularán productos matriciales ni consultarán modelos directamente.

Alternativas consideradas: colocar la orquestación directamente en vistas violaría el requisito de vistas delgadas y produciría pruebas acopladas a HTTP.

### Contratos HTTP

Se conservarán las rutas `/`, `/api/scenarios/`, `/api/simulate/`, `/api/validate/` y `/api/history/`. Las solicitudes POST requerirán CSRF. Los errores de entrada serán HTTP 400; los métodos no admitidos serán 405.

Las respuestas JSON contendrán los nombres de campos definidos por las capacidades. Los mensajes de error serán legibles en español y podrán incluir `invalid_rows`.

### Interacción de matriz

`matrix.js` validará localmente cada cambio con debounce de 300 ms y enviará al endpoint de validación. `api.js` será responsable de las llamadas fetch y envío de CSRF. `charts.js` consumirá la trayectoria y distribución y renderizará Chart.js.

Se usarán tolerance de cliente 0.001 y tolerancia servidor 1e-9. Los valores visibles se redondearán a cuatro decimales sin modificar internamente la matriz completa.

Alternativas consideradas: una validación exclusiva en servidor sería más lenta y menos visible; una validación exclusiva en cliente no protegería integraciones externas.

### Plantillas y presentación

`base.html` contendrá layout y carga de Chart.js. `index.html` contendrá la página principal. `partials/matrix_editor.html` y `partials/results_table.html` aislarán componentes. Los parciales no ejecutarán cálculo ni consultas.

Todo el texto visible estará en español; los horizontes mostrarán pasos y equivalencia temporal.

### Estrategia de pruebas y trazabilidad

Las pruebas seguirán TDD: primero pruebas rojas, luego implementación mínima y refactor. Las pruebas se distribuirán en `test_markov.py`, `test_models.py`, `test_services.py`, `test_api.py` y `test_views.py`.

Cada requisito Scenario tendrá al menos una prueba identificable con su ID en el nombre o documentación de la prueba. La cobertura global objetivo será al menos 80 % y el motor tendrá 100 % de cobertura.

### Flujo SDD/OpenSpec

El flujo de trabajo será:

1. Ejecutar `openspec init` y completar `openspec/project.md` con stack MVT, convenciones y comandos de prueba.
2. Por fase: crear propuesta con `proposal.md`, `tasks.md`, `design.md` y deltas en `specs/`.
3. Ejecutar `openspec validate <change-id> --strict`.
4. Aplicar la fase guiada por `tasks.md`.
5. Ejecutar `openspec archive` al finalizar la fase.

El agente SHALL observar estas reglas: no modificar specs sin dejarlo en el change, no saltarse tareas, escribir pruebas antes del código y no tocar capas fuera del alcance de la fase.

## Risks / Trade-offs

- [Matrices mal condicionadas o redondeadas] → Validar con tolerancia 1e-9 en servidor y 0.001 en cliente.
- [Solicitudes excesivas durante edición] → Debounce de 300 ms y validación local previa.
- [Diferencias entre CDN y entorno sin red] → Usar Chart.js desde CDN o considerar archivo local sin cambiar el contrato.
- [Datos de escenarios interpretados como reales] → Mostrar aviso didáctico en interfaz y README.
- [Agente modificando fuera del alcance] → Revisar el diff por fase y respetar las tareas MVT.
- [Inconsistencia entre código y especificación] → Nombrar pruebas por ID de Scenario y ejecutar validación estricta.

## Migration Plan

1. Crear el proyecto Django y la app `simulator`.
2. Crear y aplicar migraciones de `Scenario` y `Simulation`.
3. Ejecutar la migración de datos con los tres escenarios base.
4. Verificar compatibilidad con SQLite antes de continuar a vistas y templates.
5. Si una migración falla, revertir la migración o el commit de la fase antes de continuar.

## Open Questions

Ninguna. Las matrices didácticas de los tres escenarios se asumirán como datos de ejemplo y no como mediciones reales hasta que existan requisitos posteriores que las definan.

# Spec Delta

## Purpose

Define las rutas, respuestas y errores HTTP de las vistas del simulador, manteniendo las vistas delgadas y delegando cálculo y persistencia a servicios y dominio.

## ADDED Requirements

### Requirement: Página principal
El sistema SHALL responder 200 en `GET /` con HTML que incluya los escenarios disponibles en el contexto.

#### Scenario: Solicitud anónima válida
- **WHEN** un cliente realiza GET a `/`
- **THEN** recibe HTML 200 con el selector de escenario y el estado inicial disponible

### Requirement: API de escenarios
El sistema SHALL responder JSON a `GET /api/scenarios/` con los escenarios persistidos.

#### Scenario: Consulta exitosa
- **WHEN** un cliente realiza GET a `/api/scenarios/`
- **THEN** recibe estado 200 y los datos de nombre, slug, descripción y matriz de los escenarios

### Requirement: API de simulación
El sistema SHALL aceptar POST en `/api/simulate/` y devolver `{results, trajectory, interpretation}` al recibir una entrada válida.

#### Scenario: Simulación válida
- **WHEN** el cliente envía una matriz válida, un estado inicial válido y los horizontes admitidos
- **THEN** recibe estado 200 con resultados, trayectoria e interpretación

#### Scenario: Entrada inválida
- **WHEN** el cliente envía datos que no pasan la validación
- **THEN** recibe estado 400 con `{"error": "...", "invalid_rows": [i]}` cuando existen filas inválidas

### Requirement: API de validación
El sistema SHALL aceptar POST en `/api/validate/` y devolver `{valid, invalid_rows}`.

#### Scenario: Matriz válida
- **WHEN** se valida una matriz estocástica 4x4 por el endpoint
- **THEN** devuelve estado 200 con `valid: true` y una lista de filas vacía

#### Scenario: Matriz inválida
- **WHEN** se valida una matriz con filas inválidas
- **THEN** devuelve estado 400 con `valid: false` y los índices de las filas inválidas

### Requirement: API de historial
El sistema SHALL responder JSON a `GET /api/history/` con las simulaciones recientes.

#### Scenario: Consulta exitosa
- **WHEN** un cliente realiza GET a `/api/history/`
- **THEN** recibe las últimas simulaciones disponibles, como máximo veinte

### Requirement: Métodos no permitidos
El sistema SHALL responder 405 cuando una ruta reciba un método HTTP no admitido.

#### Scenario: POST a una ruta exclusiva GET
- **WHEN** se envía POST a `/api/scenarios/` o `/api/history/`
- **THEN** el sistema responde 405

#### Scenario: GET a una ruta exclusiva POST
- **WHEN** se envía GET a `/api/simulate/` o `/api/validate/`
- **THEN** el sistema responde 405

### Requirement: Protección CSRF
Los endpoints POST SHALL exigir y aceptar el token CSRF suministrado por el JavaScript desde el template.

#### Scenario: Solicitud POST sin token
- **WHEN** un cliente realiza una solicitud POST sin token CSRF válido
- **THEN** Django rechaza la solicitud según su protección CSRF

#### Scenario: Solicitud POST con token
- **WHEN** el JavaScript envía el token CSRF del template junto con datos válidos
- **THEN** el endpoint procesa la solicitud

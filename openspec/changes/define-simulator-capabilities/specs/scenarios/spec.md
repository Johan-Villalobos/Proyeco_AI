# Spec Delta

## Purpose

Define la persistencia y recuperación de los tres escenarios preestablecidos, las simulaciones realizadas y el historial reciente del simulador de congestión.

## ADDED Requirements

### Requirement: Modelo de escenario
El sistema SHALL persistir cada escenario con nombre único, slug único, descripción, matriz 4x4 e indicador de si es preestablecido.

#### Scenario: Escenario válido
- **WHEN** se crea un escenario con los cinco datos requeridos y una matriz estocástica válida
- **THEN** el escenario queda almacenado

#### Scenario: Nombre o slug duplicado
- **WHEN** se intenta guardar un nombre o slug ya existente
- **THEN** el sistema rechaza la operación por la restricción de unicidad

### Requirement: Escenarios base
El sistema SHALL incluir los escenarios base "Hora pico mañana", "Día lluvioso" y "Domingo/Festivo", con slug único y matriz 4x4.

#### Scenario: Migración inicial
- **WHEN** se ejecuta la migración de datos 0002_seed_scenarios.py
- **THEN** quedan cargados los tres escenarios base sin duplicarlos

#### Scenario: Consulta de escenarios
- **WHEN** se listan los escenarios disponibles
- **THEN** aparecen los tres escenarios base con nombre, descripción y matriz

### Requirement: Validación de matriz del escenario
El sistema SHALL reutilizar la validación del motor de Markov al limpiar un modelo que contenga una matriz.

#### Scenario: Matriz válida en Scenario
- **WHEN** se limpia un escenario con forma 4x4, valores válidos y filas que suman 1
- **THEN** la limpieza del modelo se acepta

#### Scenario: Matriz inválida en Scenario
- **WHEN** se limpia un escenario cuya matriz no cumple las reglas estocásticas
- **THEN** la limpieza falla con la información de las filas inválidas cuando corresponda

### Requirement: Registro de simulación
El sistema SHALL guardar el estado inicial, la matriz realmente utilizada, los resultados a 1, 3, 5 y 10 pasos y la fecha de creación de cada simulación.

#### Scenario: Simulación basada en escenario
- **WHEN** se completa una simulación seleccionando un escenario y un estado inicial válido
- **THEN** se registra la referencia al escenario y una copia de la matriz utilizada

#### Scenario: Simulación con matriz editada
- **WHEN** se completa una simulación usando una matriz editada sin escenario asociado
- **THEN** se registra la simulación con la referencia de escenario nula y la matriz editada

### Requirement: Historial reciente
El sistema SHALL devolver como máximo las últimas 20 simulaciones ordenadas desde la más reciente.

#### Scenario: Solicitud con menos de veinte simulaciones
- **WHEN** existen menos de veinte simulaciones
- **THEN** el historial contiene todas las simulaciones disponibles

#### Scenario: Solicitud con más de veinte simulaciones
- **WHEN** existen más de veinte simulaciones
- **THEN** el historial contiene solamente las veinte simulaciones más recientes

### Requirement: Operación de servicios
El sistema SHALL ofrecer operaciones separadas para obtener escenarios, ejecutar una simulación, guardarla y consultar el historial.

#### Scenario: Ejecución correcta
- **WHEN** se proporcionan una matriz válida, un estado inicial válido y pasos admitidos
- **THEN** el servicio entrega resultados y trayectoria sin exigir conocimientos de request o response HTTP

#### Scenario: Datos inválidos
- **WHEN** se proporcionan datos que no pasan la validación
- **THEN** el servicio rechaza la operación antes de persistir una simulación

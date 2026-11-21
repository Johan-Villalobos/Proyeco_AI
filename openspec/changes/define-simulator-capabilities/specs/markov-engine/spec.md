# Spec Delta

## Purpose

Define el comportamiento observable del dominio de cadenas de Markov sin dependencias de Django, incluyendo validación de matrices, cálculo de distribuciones y generación de trayectorias.

## ADDED Requirements

### Requirement: Estados de congestión
El motor SHALL exponer, en orden, los estados `Fluido`, `Moderado`, `Congestionado` y `Colapsado`, identificados también por los índices 0, 1, 2 y 3.

#### Scenario: Consulta del catálogo de estados
- **WHEN** una operación solicita la lista de estados
- **THEN** el motor entrega exactamente los cuatro estados en el orden indicado

### Requirement: Validación de matriz estocástica
El motor SHALL validar que una matriz tenga exactamente 4 filas y 4 columnas, que sus valores estén en el intervalo [0,1] y que cada fila sume 1 con una tolerancia de 1e-9.

#### Scenario: Matriz válida
- **WHEN** se valida una matriz 4x4 con valores entre 0 y 1 y filas que suman 1
- **THEN** la matriz es aceptada

#### Scenario: Forma inválida
- **WHEN** se valida una matriz cuyo número de filas o columnas no sea 4
- **THEN** la validación falla con un error que identifica el problema de forma

#### Scenario: Valores fuera del intervalo
- **WHEN** una celda de la matriz contiene un valor menor que 0 o mayor que 1
- **THEN** la validación falla indicando que la matriz no contiene probabilidades válidas

#### Scenario: Filas inválidas
- **WHEN** al menos una fila no suma 1 dentro de la tolerancia 1e-9
- **THEN** la validación falla y el resultado identifica los índices de las filas inválidas

### Requirement: Vector inicial one-hot
El motor SHALL crear un vector de distribución inicial con 1 en el índice indicado y 0 en los otros tres índices.

#### Scenario: Estado inicial Fluido
- **WHEN** se solicita el vector inicial para el índice 0
- **THEN** el motor entrega `[1, 0, 0, 0]`

#### Scenario: Estado inicial Colapsado
- **WHEN** se solicita el vector inicial para el índice 3
- **THEN** el motor entrega `[0, 0, 0, 1]`

#### Scenario: Índice fuera de rango
- **WHEN** se solicita un índice menor que 0 o mayor que 3
- **THEN** el motor rechaza la solicitud

### Requirement: Distribución después de pasos
El motor SHALL calcular la distribución multiplicando el vector por la matriz en el orden correcto y SHALL producir resultados para los horizontes 1, 3, 5 y 10.

#### Scenario: Un paso desde un estado conocido
- **WHEN** se calcula una distribución con el vector inicial y n igual a 1
- **THEN** el resultado corresponde a la fila de transición asociada al estado inicial

#### Scenario: Horizonte cero
- **WHEN** se solicita la distribución para n igual a 0
- **THEN** el motor entrega el vector inicial sin modificarlo

#### Scenario: Horizontes completos
- **WHEN** se solicita una simulación con horizontes 1, 3, 5 y 10
- **THEN** el resultado contiene una distribución para cada horizonte

#### Scenario: Identidad
- **WHEN** se usa una matriz identidad y cualquier distribución inicial
- **THEN** la distribución permanece igual en todos los pasos

#### Scenario: Estado absorbente
- **WHEN** se usa una matriz con un estado absorbente y se alcanza dicho estado
- **THEN** la distribución posterior conserva masa 1 en ese estado

### Requirement: Trayectoria de distribución
El motor SHALL calcular la trayectoria completa desde π(0) hasta el máximo solicitado y SHALL permitir construir una evolución gráfica.

#### Scenario: Trayectoria hasta diez pasos
- **WHEN** se solicita una trayectoria con máximo 10
- **THEN** el motor entrega once distribuciones, una para cada paso desde 0 hasta 10

### Requirement: Distribución estacionaria opcional
El motor SHALL calcular una distribución estacionaria cuando pueda resolverse para la matriz suministrada.

#### Scenario: Matriz reducible o sin solución numérica estable
- **WHEN** no puede determinarse una distribución estacionaria única o estable
- **THEN** el motor devuelve un resultado que indica la condición, sin alterar las distribuciones calculadas

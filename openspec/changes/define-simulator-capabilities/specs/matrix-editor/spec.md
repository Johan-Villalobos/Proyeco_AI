# Spec Delta

## Purpose

Define el editor interactivo de matrices 4x4, su validación local, el restablecimiento y la comunicación liviana con la API de validación y simulación.

## ADDED Requirements

### Requirement: Entrada editable 4x4
La interfaz SHALL presentar 16 inputs numéricos organizados en una matriz 4x4 y SHALL incluir una columna con la suma calculada por fila.

#### Scenario: Carga inicial
- **WHEN** se abre el editor con un escenario seleccionado
- **THEN** se muestran 16 inputs con los valores de la matriz y 4 sumas de fila

#### Scenario: Cambio manual
- **WHEN** el usuario modifica una celda
- **THEN** el valor mostrado cambia y se inicia la validación de la matriz completa

### Requirement: Validación en vivo
El editor SHALL validar que los valores estén entre 0 y 1 y que las filas sumen 1 con una tolerancia de cliente de 0.001.

#### Scenario: Matriz válida
- **WHEN** todas las celdas están dentro del intervalo y todas las sumas están dentro de la tolerancia
- **THEN** el indicador visible cambia a verde

#### Scenario: Matriz inválida
- **WHEN** una celda está fuera del intervalo o una suma excede la tolerancia
- **THEN** el indicador visible cambia a rojo y la fila inválida se identifica visualmente

### Requirement: Antirrebote de validación
Las validaciones iniciadas por cambios sucesivos SHALL esperar 300 ms antes de enviarse para evitar solicitudes excesivas.

#### Scenario: Edición rápida
- **WHEN** el usuario modifica varias celdas durante menos de 300 ms
- **THEN** se realiza una sola solicitud después de transcurrir el período de espera sin cambios adicionales

### Requirement: Restablecimiento
El editor SHALL permitir restablecer la matriz al escenario seleccionado.

#### Scenario: Restablecer matriz editada
- **WHEN** el usuario pulsa Restablecer después de modificar celdas
- **THEN** los 16 inputs vuelven a los valores de la matriz del escenario seleccionado

#### Scenario: Restablecer sin escenario asociado
- **WHEN** el usuario pulsa Restablecer mientras usa una matriz creada sin escenario
- **THEN** el sistema devuelve un estado seguro definido para el editor sin modificar datos persistidos

### Requirement: Integración con simulación
El editor SHALL enviar la matriz editada a la API de simulación junto con el estado inicial seleccionado.

#### Scenario: Simulación con matriz válida
- **WHEN** el usuario pulsa Simular y la matriz es válida
- **THEN** el cliente envía la matriz y el estado inicial y muestra la respuesta

#### Scenario: Simulación con matriz inválida
- **WHEN** el usuario pulsa Simular y la matriz no es válida
- **THEN** el cliente evita el envío y conserva visible el error de validación

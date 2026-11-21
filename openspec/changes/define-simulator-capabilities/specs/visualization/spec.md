# Spec Delta

## Purpose

Define la presentación en español de la simulación, los resultados por horizonte y las gráficas de distribución y evolución temporal.

## ADDED Requirements

### Requirement: Página en español
La interfaz SHALL presentar todos los textos visibles en español y SHALL mostrar los tiempos como minutos y horas.

#### Scenario: Contenido principal
- **WHEN** se carga la página
- **THEN** la interfaz incluye selector de escenario, estado inicial, matriz editable y zona de resultados con etiquetas en español

#### Scenario: Conversión de horizonte
- **WHEN** se presenta el horizonte 3
- **THEN** la interfaz muestra 3 pasos y su equivalente de 1.5 horas

### Requirement: Tabla de resultados
La interfaz SHALL mostrar una tabla con una fila por horizonte 1, 3, 5 y 10 y una columna por cada estado de congestión.

#### Scenario: Simulación completa
- **WHEN** llega una respuesta válida con los cuatro horizontes
- **THEN** la tabla contiene cuatro filas y cuatro columnas de estado con distribuciones legibles

#### Scenario: Redondeo
- **WHEN** un resultado contiene más de cuatro decimales
- **THEN** la interfaz muestra el valor redondeado a cuatro decimales

### Requirement: Gráfica de barras
La interfaz SHALL mostrar una gráfica de barras de la distribución por cada horizonte seleccionado.

#### Scenario: Resultado disponible
- **WHEN** se recibe una distribución válida
- **THEN** la gráfica representa los cuatro estados y permite distinguir su proporción en el horizonte mostrado

### Requirement: Gráfica de líneas
La interfaz SHALL mostrar la evolución desde π(0) hasta π(10), con una línea por estado.

#### Scenario: Trayectoria disponible
- **WHEN** llega una trayectoria completa de 0 a 10
- **THEN** la gráfica contiene la evolución de los cuatro estados en el eje temporal

### Requirement: Interpretación didáctica
La interfaz SHALL presentar una interpretación textual de los resultados y SHALL indicar que las probabilidades son didácticas y no datos reales.

#### Scenario: Simulación completada
- **WHEN** se muestran los resultados
- **THEN** la interfaz incluye texto interpretativo y el aviso de uso didáctico

### Requirement: Componentes de plantilla
La interfaz SHALL mantener el layout y los parciales separados, sin reglas de negocio ni consultas a la base de datos dentro de las plantillas.

#### Scenario: Renderizado principal
- **WHEN** se renderiza `index.html`
- **THEN** la plantilla extiende `base.html` y usa parciales para el editor y la tabla de resultados

#### Scenario: Contenido esperado
- **WHEN** se solicita la página principal
- **THEN** el resultado contiene el selector de escenario, 16 inputs de matriz y contenedores de gráficas

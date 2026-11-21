# Simulador de congestión vial

Aplicación educativa que usa una cadena de Markov para estimar la distribución de
probabilidades de cuatro estados del tráfico en bloques de 30 minutos. Se puede
seleccionar un escenario, editar su matriz de transición y observar resultados a
1, 3, 5 y 10 pasos, junto con una trayectoria y un historial de simulaciones.

> **Aviso:** los escenarios y sus matrices son valores ilustrativos didácticos.
> No representan mediciones ni predicciones basadas en datos reales.

## Requisitos

- Python 3.10 o posterior.
- pip.
- Conexión a Internet para cargar Chart.js 4.4.7 desde su CDN.

La aplicación usa SQLite por defecto; no hace falta instalar ni configurar un
servidor de base de datos.

## Instalación

Desde la carpeta del proyecto, crea y activa un entorno virtual e instala las
dependencias:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

En macOS o Linux, activa el entorno con:

```sh
source .venv/bin/activate
```

## Migraciones y ejecución

Aplica las migraciones para crear la base de datos SQLite y cargar los tres
escenarios iniciales:

```powershell
python manage.py migrate
```

Inicia el servidor de desarrollo:

```powershell
python manage.py runserver
```

Abre <http://127.0.0.1:8000/> en el navegador.

## Pruebas

Ejecuta la suite automatizada de Django:

```powershell
python manage.py test
```

Comprueba también la configuración del proyecto:

```powershell
python manage.py check
```

## Escenarios incluidos

Las matrices de transición son ejemplos didácticos creados para explorar el
comportamiento del modelo; no son datos observados de tráfico.

- **Hora pico mañana:** alta demanda, con mayor tendencia a congestionarse y
  recuperación lenta.
- **Día lluvioso:** condiciones ilustrativas de menor velocidad y mayor riesgo
  de congestión o colapso.
- **Domingo/Festivo:** demanda baja, con mayor probabilidad de permanecer fluido
  y recuperarse rápidamente.

Cada paso representa 30 minutos. Los horizontes mostrados corresponden a
30 minutos, 1.5 horas, 2.5 horas y 5 horas.

## Estructura del proyecto

```text
config/                         Configuración, URLs y WSGI de Django
simulator/
  markov.py                     Operaciones de dominio de la cadena de Markov
  models.py                     Modelos Scenario y Simulation
  services.py                   Orquestación de escenarios y simulaciones
  views.py                      Vistas HTML y endpoints JSON
  urls.py                       Rutas de la aplicación
  migrations/                   Esquema y escenarios de ejemplo
  templates/simulator/          Página, layout y parciales MVT
  static/simulator/css/         Estilos responsive
  static/simulator/js/          API, editor de matriz y gráficas
  tests/                        Pruebas automatizadas
manage.py                       Utilidad de administración de Django
requirements.txt                Dependencias de Python
```

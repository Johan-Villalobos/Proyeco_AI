# PLAN DE INGENIERÍA: Simulador de Tráfico y Congestión Vial (Cadenas de Markov)

> Documento de planeación técnica previo a la implementación (SDD + OpenSpec).
> Complementa a `SPECS_SIMULADOR_TRAFICO.md`: allí se define **qué** hace el sistema; aquí se define **cómo** se construye, organizado bajo el patrón **MVT (Model-View-Template)** de Django.

---

## 1. Resumen del proyecto

| Elemento | Detalle |
|---|---|
| Problema | Predicción del nivel de congestión de un corredor vial principal |
| Técnica | Cadena de Markov discreta (bloques de 30 min) |
| Estados | `Fluido`, `Moderado`, `Congestionado`, `Colapsado` |
| Escenarios | Hora pico mañana, Día lluvioso, Domingo/Festivo |
| Horizontes | 1, 3, 5 y 10 pasos (30 min, 1.5 h, 2.5 h, 5 h) |
| Framework | Django (patrón MVT) |
| Base de datos | SQLite (la configurada por defecto) |
| Gráficas | Chart.js (en el Template) |
| Metodología | SDD con OpenSpec, desarrollo asistido por agente de IA |
| Control de versiones | Git + GitHub (ramas por cambio, PRs, CI) |

## 2. Principios de diseño

1. **Especificar antes de programar:** ningún código sin su change de OpenSpec aprobado.
2. **MVT estricto, con una capa de dominio aparte:** la matemática de Markov vive fuera de Django para poder probarla en aislamiento.
3. **Vistas delgadas:** las vistas orquestan; la lógica está en `markov.py` y `services.py`.
4. **Plantillas sin lógica de negocio:** solo presentación y JavaScript de interacción.
5. **Pruebas primero (TDD)** en el motor y la API.
6. **Cambios pequeños y trazables:** un change = una rama = un PR.

## 3. Arquitectura MVT

### 3.1 Vista general

```
 Navegador (Template + JS + Chart.js)
        │  GET /                      → HTML
        │  POST /api/simulate/ (JSON) → resultados
        ▼
 urls.py  ──►  View (views.py)
                 │ valida entrada
                 ▼
              services.py ──► markov.py   (dominio puro, sin Django)
                 │
                 ▼
              Model (models.py) ──► SQLite
                 │
        View arma contexto / JSON
                 ▼
        Template (index.html) renderiza
```

### 3.2 Responsabilidad de cada capa

| Capa MVT | Archivo(s) | Responsabilidad | Prohibido |
|---|---|---|---|
| **Model** | `simulator/models.py` | Definir `Scenario` y `Simulation`; persistir matrices y resultados | Cálculos de Markov, lógica de UI |
| **View** | `simulator/views.py` | Recibir petición, validar, llamar a `services`, devolver `HttpResponse`/`JsonResponse` | Multiplicar matrices, armar HTML a mano |
| **Template** | `simulator/templates/simulator/*.html`, `static/` | Mostrar selectores, matriz editable, tablas y gráficas | Reglas de negocio, consultas a BD |
| **Dominio** (apoyo) | `simulator/markov.py` | Validar matriz, calcular `π(n)`, trayectoria, estacionaria | Importar Django |
| **Servicios** (apoyo) | `simulator/services.py` | Conectar dominio con modelos (cargar escenario, guardar simulación) | Manejar request/response |

> `markov.py` y `services.py` no son parte formal de MVT; son capas de apoyo que mantienen las vistas delgadas y el dominio testeable.

### 3.3 Estructura de carpetas

```
traffic_markov/
├── manage.py
├── requirements.txt
├── README.md
├── PLAN_INGENIERIA.md
├── SPECS_SIMULADOR_TRAFICO.md
├── .gitignore
├── .github/workflows/tests.yml
├── openspec/
│   ├── project.md
│   ├── specs/
│   └── changes/
├── config/
│   ├── settings.py            # SQLite por defecto, idioma es-co, zona America/Bogota
│   ├── urls.py                # include('simulator.urls')
│   └── wsgi.py
└── simulator/
    ├── __init__.py
    ├── apps.py
    ├── markov.py              # DOMINIO
    ├── services.py            # SERVICIOS
    ├── models.py              # MODEL
    ├── views.py               # VIEW
    ├── urls.py
    ├── admin.py
    ├── migrations/
    │   ├── 0001_initial.py
    │   └── 0002_seed_scenarios.py
    ├── templates/simulator/   # TEMPLATE
    │   ├── base.html
    │   ├── index.html
    │   └── partials/
    │       ├── matrix_editor.html
    │       └── results_table.html
    ├── static/simulator/
    │   ├── css/styles.css
    │   └── js/
    │       ├── api.js         # llamadas fetch
    │       ├── matrix.js      # edición y validación en cliente
    │       └── charts.js      # Chart.js
    └── tests/
        ├── test_markov.py
        ├── test_models.py
        ├── test_services.py
        ├── test_api.py
        └── test_views.py
```

## 4. Diseño por capa

### 4.1 Model (`models.py`)

**`Scenario`**
| Campo | Tipo | Nota |
|---|---|---|
| `name` | CharField(80, unique) | "Hora pico mañana" |
| `slug` | SlugField(unique) | `hora-pico-manana` |
| `description` | TextField | Supuestos del escenario |
| `matrix` | JSONField | 4x4, filas suman 1 |
| `is_preset` | BooleanField | True para los 3 base |

**`Simulation`**
| Campo | Tipo | Nota |
|---|---|---|
| `scenario` | FK(Scenario, null=True, SET_NULL) | Nulo si la matriz fue editada |
| `initial_state` | PositiveSmallIntegerField | 0 a 3 |
| `matrix` | JSONField | Matriz realmente usada |
| `results` | JSONField | `{"1":[..],"3":[..],"5":[..],"10":[..]}` |
| `created_at` | DateTimeField(auto_now_add) | |

Reglas: validación de forma 4x4 y suma de filas en `clean()` reutilizando `markov.validate_matrix`. Escenarios base cargados con la data migration `0002_seed_scenarios.py`.

### 4.2 Dominio (`markov.py`)

Funciones puras, sin Django:

| Función | Descripción |
|---|---|
| `STATES` | Tupla ordenada de los 4 estados |
| `validate_matrix(m)` | Verifica 4x4, valores en [0,1], filas suman 1 (tol. 1e-9); lanza `MatrixError` con filas inválidas |
| `initial_vector(state_index)` | Vector one-hot |
| `step(vector, matrix)` | Un paso: `v · P` |
| `distribution_at(vector, matrix, n)` | `π(n)` |
| `trajectory(vector, matrix, max_n)` | Lista de `π(0..max_n)` para la gráfica de líneas |
| `stationary(matrix)` | Distribución estacionaria (opcional) |

Decisión de implementación: Python puro con listas (4x4 es trivial, evita dependencia). Se registrará en `design.md` del change `add-markov-engine`.

### 4.3 Servicios (`services.py`)

| Función | Descripción |
|---|---|
| `get_scenarios()` | Devuelve escenarios con su matriz |
| `run_simulation(matrix, initial_state, steps)` | Valida, calcula resultados y trayectoria |
| `save_simulation(...)` | Persiste `Simulation` |
| `recent_history(limit=20)` | Últimas simulaciones |

### 4.4 View (`views.py`) y rutas (`urls.py`)

| Ruta | Método | Vista | Respuesta |
|---|---|---|---|
| `/` | GET | `IndexView` (TemplateView) | HTML con escenarios en el contexto |
| `/api/scenarios/` | GET | `scenarios_api` | JSON |
| `/api/simulate/` | POST | `simulate_api` | JSON `{results, trajectory, interpretation}` |
| `/api/validate/` | POST | `validate_api` | JSON `{valid, invalid_rows}` |
| `/api/history/` | GET | `history_api` | JSON |

Contrato de errores: HTTP 400 con `{"error": "...", "invalid_rows": [i]}`; 405 para método no permitido. Los endpoints POST usan CSRF (el JS envía el token del template).

### 4.5 Template (`templates/` y `static/`)

- `base.html`: layout, carga de Chart.js y estáticos, bloque `content`.
- `index.html` (extiende `base.html`): selector de escenario y estado, matriz editable, botón Simular, zona de resultados.
- `partials/matrix_editor.html`: tabla 4x4 con inputs numéricos (step 0.01) y columna de suma por fila.
- `partials/results_table.html`: tabla n × estado.
- `charts.js`: gráfica de barras (distribución por n) y de líneas (evolución 0..10).
- `matrix.js`: validación en cliente, indicador verde/rojo, recálculo con debounce (300 ms), restablecer.
- Todo el texto en español; los tiempos se muestran como minutos y horas.

## 5. Plan de ejecución por fases

| Fase | Change OpenSpec | Capa MVT principal | Entregable | Pruebas |
|---|---|---|---|---|
| F0 | `setup-project` | Configuración | Repo, venv, Django, app `simulator`, OpenSpec init | `manage.py check` |
| F1 | `add-markov-engine` | Dominio | `markov.py` | `test_markov.py` |
| F2 | `add-scenarios-persistence` | **Model** | Modelos, migraciones, seed, `services.py` | `test_models.py`, `test_services.py` |
| F3 | `add-simulation-api` | **View** | Endpoints y `urls.py` | `test_api.py` |
| F4 | `add-web-ui-charts` | **Template** | Página, tablas, gráficas | `test_views.py` |
| F5 | `add-live-matrix-editor` | Template + View | Edición en vivo y validación | Pruebas de API/vista + checklist manual |
| F6 | `add-ci-and-docs` | Transversal | CI, cobertura, README, archivado | Pipeline verde |

Dependencias: F1 → F2 → F3 → F4 → F5 → F6. Dentro de cada fase: spec → pruebas (rojas) → implementación (verde) → refactor → commit → PR.

## 6. Estrategia de pruebas

| Nivel | Qué valida | Herramienta |
|---|---|---|
| Unitario (dominio) | Cálculo de `π(n)`, validación, casos borde (identidad, absorbente, n=0) | `django.test.SimpleTestCase` o pytest |
| Modelo | Restricciones, seed de 3 escenarios, `clean()` | `django.test.TestCase` |
| Servicios | Orquestación y persistencia | `TestCase` |
| API / Vista | Códigos 200/400/405, contrato JSON, CSRF | `Client` de Django |
| Template | Página contiene escenarios, inputs 4x4 y contenedores de gráficas | `assertContains` |
| Trazabilidad | Cada Scenario de OpenSpec tiene al menos una prueba (nombrar tests con el ID, p. ej. `test_rf03_un_paso`) | Revisión en F6 |

Metas: cobertura ≥ 80 % global y 100 % en `markov.py`. Valores esperados de referencia calculados a mano para el escenario "Hora pico mañana".

## 7. Flujo SDD / OpenSpec

1. `openspec init` y completar `openspec/project.md` (stack MVT, convenciones, comandos de prueba).
2. Por fase: `/openspec:proposal` → `proposal.md`, `tasks.md`, `design.md`, deltas en `specs/`.
3. `openspec validate <change-id> --strict`.
4. `/openspec:apply` guiado por `tasks.md`.
5. `/openspec:archive` al finalizar la fase.

Reglas para el agente de IA: no modificar specs sin dejarlo en el change, no saltarse tareas, escribir pruebas antes del código y no tocar capas fuera del alcance de la fase.

## 8. Git y GitHub

- Ramas: `main` estable, `feat/<change-id>` por fase.
- Commits convencionales: `docs(spec):`, `test:`, `feat:`, `refactor:`, `chore:`.
- Orden por cambio: commit de spec → commit de pruebas → commit de implementación.
- PR por fase con enlace al change y checklist de tareas completadas.
- GitHub Actions (`tests.yml`): instalar dependencias, `python manage.py test`, reporte de cobertura.
- `.gitignore`: `db.sqlite3`, `.venv/`, `__pycache__/`, `node_modules/`, `.coverage`.

## 9. Configuración técnica

- Python 3.11+ y Django 5.x.
- `settings.py`: `DATABASES` por defecto (SQLite), `LANGUAGE_CODE = "es-co"`, `TIME_ZONE = "America/Bogota"`, `INSTALLED_APPS` incluye `simulator`.
- Dependencias mínimas: `Django`, `coverage` (o `pytest-django` + `pytest-cov`).
- Chart.js por CDN en `base.html` (o archivo local en `static/` para no depender de red).
- Comandos de trabajo:
  ```
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py runserver
  python manage.py test
  coverage run manage.py test && coverage report
  ```

## 10. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Errores de redondeo hacen que filas no sumen 1 | Validación falla en UI | Tolerancia 1e-9 en servidor y 0.001 en cliente; redondeo a 4 decimales al mostrar |
| El agente genera código fuera de la spec | Pérdida de trazabilidad | Un change por fase, revisión del diff antes de cada commit |
| Lógica de negocio filtrada a vistas o templates | Pruebas difíciles | Revisión de PR con la tabla de responsabilidades (sección 3.2) |
| Edición en vivo genera muchas peticiones | Lentitud | Debounce y cálculo en servidor ligero (4x4) |
| Datos del escenario percibidos como reales | Mala interpretación | Aviso en la interfaz y README: probabilidades didácticas |

## 11. Criterios de aceptación

- [ ] Estructura MVT respetada y documentada (modelos, vistas, plantillas separados).
- [ ] 4 estados, 3 escenarios y cálculo a 1, 3, 5 y 10 pasos verificados con pruebas.
- [ ] Gráficas funcionando y matriz editable en vivo con validación.
- [ ] Specs y changes de OpenSpec presentes (activos y archivados).
- [ ] Historial de Git que muestre spec → pruebas → código.
- [ ] Cobertura ≥ 80 % y CI en verde.
- [ ] README completo (instalación, uso, capturas, modelo matemático, uso de IA y OpenSpec).

## 12. Entregables finales

1. Repositorio GitHub con código funcional.
2. Carpeta `openspec/` con especificaciones y cambios.
3. Pruebas automatizadas y reporte de cobertura.
4. `README.md`, `SPECS_SIMULADOR_TRAFICO.md` y `PLAN_INGENIERIA.md`.

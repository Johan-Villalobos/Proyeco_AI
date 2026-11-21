(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const app = document.getElementById("simulator-app");
    if (!app) return;

    const scenarioSelector = document.getElementById("scenario-selector");
    const stateSelector = document.getElementById("initial-state");
    const cells = Array.from(app.querySelectorAll("[data-matrix-cell]"));
    const status = document.getElementById("matrix-status");
    const simulateButton = document.getElementById("simulate-button");
    const resetButton = document.getElementById("reset-matrix");
    const scenarios = new Map();
    let activeScenario = null;
    let validationTimer = null;
    let validationSequence = 0;
    let matrixIsValid = false;
    scenarioSelector.disabled = true;

    function readMatrix() {
      const matrix = Array.from({ length: 4 }, function () {
        return Array(4).fill(null);
      });
      cells.forEach(function (cell) {
        const row = Number(cell.dataset.row);
        const column = Number(cell.dataset.column);
        const value = cell.value.trim() === "" ? NaN : Number(cell.value);
        matrix[row][column] = value;
      });
      return matrix;
    }

    function validateLocally(matrix) {
      const invalidRows = [];
      matrix.forEach(function (row, rowIndex) {
        const valuesAreValid = row.every(function (value) {
          return Number.isFinite(value) && value >= 0 && value <= 1;
        });
        const sum = row.reduce(function (total, value) {
          return total + (Number.isFinite(value) ? value : 0);
        }, 0);
        const valid = valuesAreValid && Math.abs(sum - 1) <= 0.001;
        if (!valid) invalidRows.push(rowIndex);

        const sumOutput = app.querySelector(
          `[data-row-sum="${rowIndex}"]`,
        );
        const rowError = app.querySelector(
          `[data-row-error="${rowIndex}"]`,
        );
        if (sumOutput) sumOutput.textContent = sum.toFixed(4);
        if (rowError) {
          rowError.textContent = valid
            ? ""
            : valuesAreValid
              ? "La fila debe sumar 1."
              : "Usa valores entre 0 y 1.";
        }
        const rowElement = app.querySelector(
          `[data-matrix-row="${rowIndex}"]`,
        );
        if (rowElement) rowElement.classList.toggle("is-invalid", !valid);
      });

      cells.forEach(function (cell) {
        const value = Number(cell.value);
        const invalid =
          cell.value.trim() === "" ||
          !Number.isFinite(value) ||
          value < 0 ||
          value > 1;
        cell.setAttribute("aria-invalid", invalid ? "true" : "false");
      });
      return invalidRows;
    }

    function setStatus(message, kind) {
      status.textContent = message;
      status.classList.remove("is-valid", "is-invalid", "is-pending");
      if (kind) status.classList.add(`is-${kind}`);
    }

    function setMatrix(values) {
      cells.forEach(function (cell) {
        const row = Number(cell.dataset.row);
        const column = Number(cell.dataset.column);
        cell.value = values[row][column];
      });
      scheduleValidation();
    }

    function scheduleValidation() {
      window.clearTimeout(validationTimer);
      validationSequence += 1;
      const sequence = validationSequence;
      matrixIsValid = false;
      simulateButton.disabled = true;

      const matrix = readMatrix();
      const invalidRows = validateLocally(matrix);
      if (invalidRows.length) {
        setStatus(
          `Matriz inválida. Revisa las filas: ${invalidRows
            .map(function (row) {
              return row + 1;
            })
            .join(", ")}.`,
          "invalid",
        );
        return;
      }

      setStatus("Validando matriz…", "pending");
      validationTimer = window.setTimeout(async function () {
        try {
          const result = await window.SimulatorApi.post(
            app.dataset.validateUrl,
            { matrix: matrix },
          );
          if (sequence !== validationSequence) return;
          if (!result.valid) {
            const rows = (result.invalid_rows || []).map(function (row) {
              return row + 1;
            });
            setStatus(
              result.error ||
                `El servidor rechazó las filas: ${rows.join(", ")}.`,
              "invalid",
            );
            return;
          }
          matrixIsValid = true;
          simulateButton.disabled = false;
          setStatus("Matriz válida. Puedes simular.", "valid");
        } catch (error) {
          if (sequence !== validationSequence) return;
          const rows =
            error.data && Array.isArray(error.data.invalid_rows)
              ? error.data.invalid_rows.map(function (row) {
                  return row + 1;
                })
              : [];
          const detail =
            rows.length && error.message.includes("Filas inválidas:")
              ? `${error.message.split(" Filas inválidas:")[0]} Filas inválidas: ${rows.join(", ")}.`
              : error.message;
          setStatus(detail, "invalid");
        }
      }, 300);
    }

    function renderResults(data) {
      const resultsSection = document.getElementById("results-section");
      const interpretation = document.getElementById("interpretation");
      interpretation.textContent = data.interpretation;
      [1, 3, 5, 10].forEach(function (horizon) {
        const distribution = data.results[String(horizon)];
        distribution.forEach(function (probability, stateIndex) {
          const resultCell = app.querySelector(
            `[data-result="${horizon}-${stateIndex}"]`,
          );
          if (resultCell) resultCell.textContent = Number(probability).toFixed(4);
        });
      });
      resultsSection.hidden = false;
      if (window.SimulatorCharts) {
        window.SimulatorCharts.render(data);
      }
    }

    async function runSimulation() {
      if (!matrixIsValid) return;
      simulateButton.disabled = true;
      setStatus("Calculando simulación…", "pending");
      try {
        const scenarioId = scenarioSelector.value;
        const data = await window.SimulatorApi.post(
          app.dataset.simulateUrl,
          {
            matrix: readMatrix(),
            initial_state: Number(stateSelector.value),
            scenario_id: scenarioId ? Number(scenarioId) : null,
          },
        );
        renderResults(data);
        setStatus("Simulación completada.", "valid");
        loadHistory();
      } catch (error) {
        setStatus(error.message, "invalid");
      } finally {
        simulateButton.disabled = !matrixIsValid;
      }
    }

    function renderHistory(simulations) {
      const list = document.getElementById("history-list");
      const historyStatus = document.getElementById("history-status");
      list.replaceChildren();
      if (!simulations.length) {
        historyStatus.textContent = "Todavía no hay simulaciones guardadas.";
        return;
      }
      historyStatus.textContent = `${simulations.length} simulación(es) reciente(s).`;
      simulations.forEach(function (simulation) {
        const item = document.createElement("li");
        item.className = "history-item";
        const details = document.createElement("div");
        const scenario = scenarios.get(simulation.scenario_id);
        const title = document.createElement("strong");
        title.textContent = scenario ? scenario.name : "Matriz personalizada";
        const detail = document.createElement("p");
        detail.className = "history-detail";
        detail.textContent = `Estado inicial: ${
          stateSelector.options[simulation.initial_state].text
        }`;
        const time = document.createElement("time");
        const date = new Date(simulation.created_at);
        time.dateTime = simulation.created_at;
        time.textContent = Number.isNaN(date.getTime())
          ? simulation.created_at
          : date.toLocaleString("es");
        details.append(title, detail);
        item.append(details, time);
        list.append(item);
      });
    }

    async function loadHistory() {
      const historyStatus = document.getElementById("history-status");
      try {
        const data = await window.SimulatorApi.get(app.dataset.historyUrl);
        renderHistory(data.simulations);
      } catch (error) {
        historyStatus.textContent = `No se pudo cargar el historial: ${error.message}`;
      }
    }

    async function loadScenarios() {
      try {
        const data = await window.SimulatorApi.get(app.dataset.scenariosUrl);
        data.scenarios.forEach(function (scenario) {
          scenarios.set(scenario.id, scenario);
        });
        scenarioSelector.disabled = false;
        activeScenario = scenarios.get(Number(scenarioSelector.value)) || null;
        if (activeScenario) {
          document.getElementById("scenario-description").textContent =
            activeScenario.description;
        }
        await loadHistory();
      } catch (error) {
        setStatus(`No se pudieron cargar los escenarios: ${error.message}`, "invalid");
        await loadHistory();
      }
    }

    scenarioSelector.addEventListener("change", function () {
      activeScenario = scenarios.get(Number(scenarioSelector.value)) || null;
      if (!activeScenario) {
        document.getElementById("scenario-description").textContent =
          "No hay un escenario seleccionado.";
        return;
      }
      document.getElementById("scenario-description").textContent =
        activeScenario.description;
      setMatrix(activeScenario.matrix);
    });

    cells.forEach(function (cell) {
      cell.addEventListener("input", scheduleValidation);
    });
    resetButton.addEventListener("click", function () {
      if (!activeScenario) {
        setStatus("Selecciona un escenario para restaurar su matriz.", "invalid");
        return;
      }
      setMatrix(activeScenario.matrix);
    });
    simulateButton.addEventListener("click", runSimulation);

    scheduleValidation();
    loadScenarios();
  });
})();

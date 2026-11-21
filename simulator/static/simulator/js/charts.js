(function () {
  "use strict";

  const states = ["Fluido", "Moderado", "Congestionado", "Colapsado"];
  const colors = ["#18764b", "#d18b16", "#d45b2a", "#b42318"];
  let trajectoryChart = null;
  let comparisonChart = null;

  function render(data) {
    if (!window.Chart) {
      throw new Error("No se pudo cargar Chart.js para mostrar las gráficas.");
    }
    const trajectory = data.trajectory;
    const horizons = [1, 3, 5, 10];
    const trajectoryDatasets = states.map(function (state, stateIndex) {
      return {
        label: state,
        data: trajectory.map(function (distribution) {
          return distribution[stateIndex];
        }),
        borderColor: colors[stateIndex],
        backgroundColor: colors[stateIndex],
        tension: 0.25,
      };
    });
    const comparisonDatasets = states.map(function (state, stateIndex) {
      return {
        label: state,
        data: horizons.map(function (horizon) {
          return data.results[String(horizon)][stateIndex];
        }),
        backgroundColor: colors[stateIndex],
      };
    });

    if (trajectoryChart) trajectoryChart.destroy();
    if (comparisonChart) comparisonChart.destroy();
    trajectoryChart = new window.Chart(
      document.getElementById("trajectory-chart"),
      {
        type: "line",
        data: {
          labels: trajectory.map(function (_, step) {
            return `${step} (${step * 30} min)`;
          }),
          datasets: trajectoryDatasets,
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          scales: {
            y: { min: 0, max: 1, title: { display: true, text: "Probabilidad" } },
            x: { title: { display: true, text: "Paso (30 min)" } },
          },
        },
      },
    );
    comparisonChart = new window.Chart(
      document.getElementById("comparison-chart"),
      {
        type: "bar",
        data: {
          labels: horizons.map(function (horizon) {
            return `${horizon} paso${horizon === 1 ? "" : "s"}`;
          }),
          datasets: comparisonDatasets,
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { min: 0, max: 1, title: { display: true, text: "Probabilidad" } },
          },
        },
      },
    );
  }

  window.SimulatorCharts = { render: render };
})();

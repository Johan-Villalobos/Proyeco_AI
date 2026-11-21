from django.test import TestCase
from django.urls import reverse

from simulator.markov import STATES
from simulator.services import HORIZON_MINUTES


class IndexViewTests(TestCase):
    def test_index_renders_with_scenario_and_initial_state_context(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(200, response.status_code)
        self.assertEqual(4, len(response.context["states"]))
        self.assertEqual(STATES, tuple(response.context["states"]))
        self.assertEqual(0, response.context["default_state"])
        self.assertEqual(3, len(response.context["scenarios"]))
        self.assertEqual(HORIZON_MINUTES, response.context["horizon_minutes"])
        self.assertEqual("Fluido", response.context["states"][0])
        self.assertEqual(16, sum(len(row["cells"]) for row in response.context["matrix_rows"]))

    def test_index_contains_editor_results_and_chart_elements(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'id="scenario-selector"')
        self.assertContains(response, 'id="initial-state"')
        self.assertContains(response, 'id="simulate-button"')
        self.assertEqual(16, response.content.count(b'data-matrix-cell="true"'))
        self.assertEqual(16, response.content.count(b'type="number"'))
        self.assertEqual(4, response.content.count(b'data-row-sum='))
        self.assertContains(response, 'id="results-table"')
        self.assertEqual(16, response.content.count(b'data-result='))
        for horizon in (1, 3, 5, 10):
            self.assertContains(response, f'id="result-row-{horizon}"')
        self.assertContains(response, 'id="trajectory-chart"')
        self.assertContains(response, 'id="comparison-chart"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, "simulator/css/styles.css")
        self.assertContains(response, "simulator/js/api.js")
        self.assertContains(response, "simulator/js/matrix.js")
        self.assertContains(response, "simulator/js/charts.js")
        self.assertContains(response, 'value="0.85"')
        self.assertContains(
            response,
            "Las probabilidades y matrices son valores ilustrativos didácticos",
        )
        self.assertContains(response, "1.5 h")
        self.assertContains(response, "2.5 h")
        self.assertContains(response, "5 h")
        for state in STATES:
            self.assertContains(response, state)

    def test_index_contains_all_preset_names_and_pinned_chart_js(self):
        response = self.client.get(reverse("index"))

        self.assertContains(response, "Hora pico mañana")
        self.assertContains(response, "Día lluvioso")
        self.assertContains(response, "Domingo/Festivo")
        self.assertContains(
            response,
            "chart.js@4.4.7/dist/chart.umd.min.js",
        )

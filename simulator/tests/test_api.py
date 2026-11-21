import json

from django.conf import settings
from django.test import Client, TestCase
from django.urls import resolve, reverse

from simulator.models import Scenario, Simulation


VALID_MATRIX = [
    [0.50, 0.35, 0.13, 0.02],
    [0.15, 0.45, 0.35, 0.05],
    [0.05, 0.25, 0.55, 0.15],
    [0.00, 0.10, 0.40, 0.50],
]

class ApiViewTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.scenario = Scenario.objects.get(slug="hora-pico-manana")

    def post_json(self, url_name, payload, with_csrf=True):
        headers = {"content_type": "application/json"}
        if with_csrf:
            response = self.client.get(reverse("index"))
            self.assertEqual(200, response.status_code)
            csrf_cookie = self.client.cookies[settings.CSRF_COOKIE_NAME].value
            headers["HTTP_X_CSRFTOKEN"] = csrf_cookie
        return self.client.post(
            reverse(url_name),
            data=json.dumps(payload),
            **headers,
        )

    def test_api_routes_resolve(self):
        expected_names = {
            "/": "index",
            "/api/scenarios/": "scenarios_api",
            "/api/simulate/": "simulate_api",
            "/api/validate/": "validate_api",
            "/api/history/": "history_api",
        }

        for path, name in expected_names.items():
            with self.subTest(path=path):
                self.assertEqual(name, resolve(path).url_name)

    def test_scenarios_api_returns_preset_details(self):
        response = self.client.get(reverse("scenarios_api"))

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual(3, len(payload["scenarios"]))
        scenario = next(
            item for item in payload["scenarios"]
            if item["slug"] == "hora-pico-manana"
        )
        self.assertEqual(VALID_MATRIX, scenario["matrix"])
        self.assertIn("name", scenario)
        self.assertIn("description", scenario)

    def test_history_api_returns_at_most_twenty_newest_simulations(self):
        for _ in range(22):
            Simulation.objects.create(
                scenario=None,
                initial_state=0,
                matrix=VALID_MATRIX,
                results={},
            )

        response = self.client.get(reverse("history_api"))

        self.assertEqual(200, response.status_code)
        simulations = response.json()["simulations"]
        self.assertEqual(20, len(simulations))
        self.assertGreater(
            simulations[0]["id"],
            simulations[-1]["id"],
        )

    def test_simulate_api_returns_distributions_for_each_required_horizon(self):
        response = self.post_json(
            "simulate_api",
            {
                "matrix": VALID_MATRIX,
                "initial_state": 0,
                "scenario_id": self.scenario.pk,
            },
        )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual({"1", "3", "5", "10"}, set(payload["results"]))
        expected = {
            "1": [0.5, 0.35, 0.13, 0.02],
            "3": [0.2229, 0.34575, 0.33827, 0.09308],
            "5": [0.1578982, 0.3156643, 0.39095558, 0.13548192],
            "10": [
                0.13234968462270402,
                0.3000921844750721,
                0.41033669939750406,
                0.15722143150472004,
            ],
        }
        for horizon, distribution in expected.items():
            with self.subTest(horizon=horizon):
                for actual_value, expected_value in zip(
                    payload["results"][horizon],
                    distribution,
                ):
                    self.assertAlmostEqual(expected_value, actual_value, places=12)
        self.assertEqual(11, len(payload["trajectory"]))
        self.assertTrue(payload["interpretation"])
        stored = Simulation.objects.get()
        self.assertEqual(self.scenario, stored.scenario)
        self.assertEqual(VALID_MATRIX, stored.matrix)

    def test_simulate_api_does_not_change_preset_for_edited_matrix(self):
        edited_matrix = [row[:] for row in VALID_MATRIX]
        edited_matrix[0] = [0.45, 0.40, 0.13, 0.02]

        response = self.post_json(
            "simulate_api",
            {
                "matrix": edited_matrix,
                "initial_state": 0,
                "scenario_id": self.scenario.pk,
            },
        )

        self.assertEqual(200, response.status_code)
        self.scenario.refresh_from_db()
        self.assertEqual(VALID_MATRIX, self.scenario.matrix)
        simulation = Simulation.objects.get()
        self.assertIsNone(simulation.scenario)
        self.assertEqual(edited_matrix, simulation.matrix)

    def test_simulate_api_rejects_invalid_matrix_without_persisting(self):
        invalid_matrix = [row[:] for row in VALID_MATRIX]
        invalid_matrix[1][0] += 0.1

        response = self.post_json(
            "simulate_api",
            {
                "matrix": invalid_matrix,
                "initial_state": 0,
            },
        )

        self.assertEqual(400, response.status_code)
        payload = response.json()
        self.assertTrue(payload["error"])
        self.assertEqual([1], payload["invalid_rows"])
        self.assertEqual(0, Simulation.objects.count())

    def test_simulate_api_rejects_negative_values_without_persisting(self):
        invalid_matrix = [row[:] for row in VALID_MATRIX]
        invalid_matrix[2][0] = -0.01

        response = self.post_json(
            "simulate_api",
            {"matrix": invalid_matrix, "initial_state": 0},
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual([2], response.json()["invalid_rows"])
        self.assertEqual(0, Simulation.objects.count())

    def test_simulate_api_rejects_invalid_initial_state(self):
        response = self.post_json(
            "simulate_api",
            {"matrix": VALID_MATRIX, "initial_state": 4},
        )

        self.assertEqual(400, response.status_code)
        self.assertTrue(response.json()["error"])
        self.assertEqual(0, Simulation.objects.count())

    def test_simulate_api_rejects_unknown_scenario(self):
        response = self.post_json(
            "simulate_api",
            {
                "matrix": VALID_MATRIX,
                "initial_state": 0,
                "scenario_id": 999999,
            },
        )

        self.assertEqual(400, response.status_code)
        self.assertTrue(response.json()["error"])
        self.assertEqual(0, Simulation.objects.count())

    def test_simulate_api_rejects_malformed_json(self):
        self.client.get(reverse("index"))
        csrf_cookie = self.client.cookies[settings.CSRF_COOKIE_NAME].value
        response = self.client.post(
            reverse("simulate_api"),
            data="{",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_cookie,
        )

        self.assertEqual(400, response.status_code)
        self.assertIn("JSON", response.json()["error"])

    def test_validate_api_accepts_valid_matrix(self):
        response = self.post_json(
            "validate_api",
            {"matrix": VALID_MATRIX},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"valid": True, "invalid_rows": []},
            response.json(),
        )

    def test_validate_api_rejects_invalid_matrix_and_reports_rows(self):
        invalid_matrix = [row[:] for row in VALID_MATRIX]
        invalid_matrix[0][0] += 0.01
        invalid_matrix[3][0] = -0.1

        response = self.post_json(
            "validate_api",
            {"matrix": invalid_matrix},
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(
            {
                "valid": False,
                "invalid_rows": [0, 3],
                "error": (
                    "Cada fila de la matriz debe contener probabilidades entre 0 y 1 "
                    "y sumar 1. Filas inválidas: 0, 3."
                ),
            },
            response.json(),
        )

    def test_post_endpoints_reject_missing_csrf_token(self):
        response = self.post_json(
            "validate_api",
            {"matrix": VALID_MATRIX},
            with_csrf=False,
        )

        self.assertEqual(403, response.status_code)

    def test_simulate_api_rejects_missing_csrf_token(self):
        response = self.post_json(
            "simulate_api",
            {"matrix": VALID_MATRIX, "initial_state": 0},
            with_csrf=False,
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual(0, Simulation.objects.count())

    def test_post_endpoints_accept_valid_csrf_token(self):
        response = self.post_json(
            "validate_api",
            {"matrix": VALID_MATRIX},
            with_csrf=True,
        )

        self.assertEqual(200, response.status_code)

    def test_get_only_endpoints_reject_post(self):
        client = Client()
        for url_name in ("scenarios_api", "history_api"):
            with self.subTest(url_name=url_name):
                response = client.post(reverse(url_name))
                self.assertEqual(405, response.status_code)

    def test_post_only_endpoints_reject_get(self):
        for url_name in ("simulate_api", "validate_api"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(405, response.status_code)

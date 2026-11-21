from django.test import TestCase

from simulator import services
from simulator.markov import MatrixError
from simulator.models import Scenario, Simulation


VALID_MATRIX = [
    [0.5, 0.3, 0.2, 0.0],
    [0.1, 0.6, 0.2, 0.1],
    [0.0, 0.2, 0.7, 0.1],
    [0.0, 0.1, 0.2, 0.7],
]


def create_scenario() -> Scenario:
    return Scenario.objects.create(
        name="Escenario de servicios",
        slug="escenario-de-servicios",
        description="Escenario para pruebas de servicios.",
        matrix=VALID_MATRIX,
    )


class ScenarioServiceTests(TestCase):
    def test_get_scenarios_returns_scenarios_with_matrices(self):
        scenario = create_scenario()

        result = list(services.get_scenarios())

        self.assertIn(scenario, result)
        self.assertEqual(VALID_MATRIX, next(item for item in result if item.pk == scenario.pk).matrix)

    def test_run_simulation_returns_fixed_horizons_and_full_trajectory(self):
        result = services.run_simulation(VALID_MATRIX, initial_state=0)

        self.assertEqual({"1", "3", "5", "10"}, set(result["results"]))
        self.assertEqual(VALID_MATRIX[0], result["results"]["1"])
        self.assertEqual(11, len(result["trajectory"]))
        for distribution in result["trajectory"]:
            self.assertAlmostEqual(1.0, sum(distribution))

    def test_run_simulation_rejects_invalid_matrix(self):
        invalid_matrix = [row[:] for row in VALID_MATRIX]
        invalid_matrix[0][0] += 0.1

        with self.assertRaises(MatrixError):
            services.run_simulation(invalid_matrix, initial_state=0)

    def test_run_simulation_rejects_invalid_state(self):
        with self.assertRaises(ValueError):
            services.run_simulation(VALID_MATRIX, initial_state=4)

    def test_save_simulation_persists_scenario_and_used_matrix(self):
        scenario = create_scenario()
        edited_matrix = [row[:] for row in VALID_MATRIX]
        edited_matrix[0] = [0.4, 0.4, 0.15, 0.05]
        results = services.run_simulation(edited_matrix, initial_state=2)

        simulation = services.save_simulation(
            scenario=None,
            initial_state=2,
            matrix=edited_matrix,
            results=results["results"],
        )

        stored = Simulation.objects.get(pk=simulation.pk)
        self.assertIsNone(stored.scenario)
        self.assertEqual(edited_matrix, stored.matrix)
        self.assertEqual(results["results"], stored.results)

    def test_save_simulation_can_reference_scenario(self):
        scenario = create_scenario()
        result = services.run_simulation(VALID_MATRIX, initial_state=0)

        simulation = services.save_simulation(
            scenario=scenario,
            initial_state=0,
            matrix=VALID_MATRIX,
            results=result["results"],
        )

        self.assertEqual(scenario, simulation.scenario)

    def test_save_simulation_rejects_invalid_matrix_before_persisting(self):
        invalid_matrix = [row[:] for row in VALID_MATRIX]
        invalid_matrix[0][0] = -0.1

        with self.assertRaises(MatrixError):
            services.save_simulation(
                scenario=None,
                initial_state=0,
                matrix=invalid_matrix,
                results={},
            )

        self.assertEqual(0, Simulation.objects.count())

    def test_recent_history_is_newest_first_and_capped_at_twenty(self):
        for _ in range(22):
            Simulation.objects.create(
                scenario=None,
                initial_state=0,
                matrix=VALID_MATRIX,
                results={},
            )

        result = list(services.recent_history(limit=50))

        self.assertEqual(20, len(result))
        self.assertEqual(
            sorted((item.pk for item in result), reverse=True),
            [item.pk for item in result],
        )

    def test_recent_history_rejects_non_positive_limit(self):
        with self.assertRaises(ValueError):
            services.recent_history(limit=0)


if __name__ == "__main__":
    import unittest

    unittest.main()

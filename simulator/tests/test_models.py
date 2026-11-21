from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from simulator.models import Scenario, Simulation


VALID_MATRIX = [
    [0.5, 0.3, 0.2, 0.0],
    [0.1, 0.6, 0.2, 0.1],
    [0.0, 0.2, 0.7, 0.1],
    [0.0, 0.1, 0.2, 0.7],
]


class ModelPersistenceTests(TestCase):
    def test_seeded_scenarios_have_valid_didactic_matrices(self):
        scenarios = Scenario.objects.filter(is_preset=True)

        self.assertEqual(
            {"Hora pico mañana", "Día lluvioso", "Domingo/Festivo"},
            {scenario.name for scenario in scenarios},
        )
        self.assertEqual(3, scenarios.count())
        for scenario in scenarios:
            with self.subTest(scenario=scenario.slug):
                self.assertEqual(4, len(scenario.matrix))
                for row in scenario.matrix:
                    self.assertEqual(4, len(row))
                    self.assertTrue(all(value >= 0 for value in row))
                    self.assertAlmostEqual(1.0, sum(row), delta=1e-9)

    def test_scenario_fields_are_persisted(self):
        scenario = Scenario.objects.create(
            name="Escenario de prueba",
            slug="escenario-prueba",
            description="Descripción del escenario.",
            matrix=VALID_MATRIX,
            is_preset=False,
        )

        stored = Scenario.objects.get(pk=scenario.pk)

        self.assertEqual("Escenario de prueba", stored.name)
        self.assertEqual("escenario-prueba", stored.slug)
        self.assertEqual("Descripción del escenario.", stored.description)
        self.assertEqual(VALID_MATRIX, stored.matrix)
        self.assertFalse(stored.is_preset)

    def test_simulation_fields_and_scenario_reference_are_persisted(self):
        scenario = Scenario.objects.create(
            name="Escenario de prueba",
            slug="escenario-prueba",
            description="Descripción del escenario.",
            matrix=VALID_MATRIX,
            is_preset=True,
        )
        results = {"1": [0.5, 0.3, 0.2, 0.0]}
        simulation = Simulation.objects.create(
            scenario=scenario,
            initial_state=0,
            matrix=VALID_MATRIX,
            results=results,
        )

        stored = Simulation.objects.get(pk=simulation.pk)

        self.assertEqual(scenario, stored.scenario)
        self.assertEqual(0, stored.initial_state)
        self.assertEqual(VALID_MATRIX, stored.matrix)
        self.assertEqual(results, stored.results)
        self.assertIsNotNone(stored.created_at)

    def test_simulation_can_exist_without_a_scenario(self):
        simulation = Simulation.objects.create(
            scenario=None,
            initial_state=3,
            matrix=VALID_MATRIX,
            results={},
        )

        self.assertIsNone(Simulation.objects.get(pk=simulation.pk).scenario)

    def test_scenario_name_and_slug_are_unique(self):
        Scenario.objects.create(
            name="Escenario de prueba",
            slug="escenario-prueba",
            description="Descripción del escenario.",
            matrix=VALID_MATRIX,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Scenario.objects.create(
                    name="Escenario de prueba",
                    slug="otro-slug",
                    description="Descripción duplicada.",
                    matrix=VALID_MATRIX,
                )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Scenario.objects.create(
                    name="Otro escenario",
                    slug="escenario-prueba",
                    description="Descripción duplicada.",
                    matrix=VALID_MATRIX,
                )

    def test_deleting_scenario_sets_simulation_reference_to_null(self):
        scenario = Scenario.objects.create(
            name="Escenario de prueba",
            slug="escenario-prueba",
            description="Descripción del escenario.",
            matrix=VALID_MATRIX,
        )
        simulation = Simulation.objects.create(
            scenario=scenario,
            initial_state=0,
            matrix=VALID_MATRIX,
            results={},
        )

        scenario.delete()
        simulation.refresh_from_db()

        self.assertIsNone(simulation.scenario)

    def test_scenario_clean_accepts_valid_transition_matrix(self):
        scenario = Scenario(
            name="Escenario válido",
            slug="escenario-valido",
            description="Descripción del escenario.",
            matrix=VALID_MATRIX,
        )

        scenario.clean()

    def test_scenario_clean_reports_invalid_transition_rows(self):
        invalid_matrix = [row[:] for row in VALID_MATRIX]
        invalid_matrix[2][0] += 0.02
        scenario = Scenario(
            name="Escenario inválido",
            slug="escenario-invalido",
            description="Descripción del escenario.",
            matrix=invalid_matrix,
        )

        with self.assertRaises(ValidationError) as raised:
            scenario.clean()

        self.assertIn("matrix", raised.exception.message_dict)
        self.assertIn("2", raised.exception.message_dict["matrix"][0])

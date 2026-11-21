import unittest

from simulator.markov import (
    STATES,
    MatrixError,
    distribution_at,
    initial_vector,
    stationary,
    step,
    trajectory,
    validate_matrix,
)


VALID_MATRIX = [
    [0.5, 0.3, 0.2, 0.0],
    [0.1, 0.6, 0.2, 0.1],
    [0.0, 0.2, 0.7, 0.1],
    [0.0, 0.1, 0.2, 0.7],
]


class ValidateMatrixTests(unittest.TestCase):
    def test_accepts_stochastic_matrix(self):
        self.assertIsNone(validate_matrix(VALID_MATRIX))

    def test_rejects_matrix_with_wrong_shape(self):
        with self.assertRaisesRegex(MatrixError, "4x4"):
            validate_matrix([[1.0, 0.0], [0.0, 1.0]])

    def test_rejects_probability_outside_unit_interval(self):
        matrix = [row[:] for row in VALID_MATRIX]
        matrix[2][1] = -0.01

        with self.assertRaises(MatrixError) as raised:
            validate_matrix(matrix)

        self.assertIn(2, raised.exception.invalid_rows)

    def test_rejects_rows_that_do_not_sum_to_one(self):
        matrix = [row[:] for row in VALID_MATRIX]
        matrix[1][0] += 0.01

        with self.assertRaises(MatrixError) as raised:
            validate_matrix(matrix)

        self.assertEqual((1,), raised.exception.invalid_rows)

    def test_accepts_row_sum_within_tolerance(self):
        matrix = [row[:] for row in VALID_MATRIX]
        matrix[0][0] += 5e-10

        self.assertIsNone(validate_matrix(matrix))

    def test_rejects_row_sum_outside_tolerance(self):
        matrix = [row[:] for row in VALID_MATRIX]
        matrix[0][0] += 2e-9

        with self.assertRaises(MatrixError) as raised:
            validate_matrix(matrix)

        self.assertEqual((0,), raised.exception.invalid_rows)


class MarkovCalculationTests(unittest.TestCase):
    def test_states_are_in_required_order(self):
        self.assertEqual(
            ("Fluido", "Moderado", "Congestionado", "Colapsado"),
            STATES,
        )

    def test_initial_vector_is_one_hot(self):
        self.assertEqual([0.0, 0.0, 0.0, 1.0], initial_vector(3))

    def test_initial_vector_rejects_out_of_range_index(self):
        with self.assertRaises(ValueError):
            initial_vector(4)

    def test_step_multiplies_vector_by_transition_matrix(self):
        result = step([1.0, 0.0, 0.0, 0.0], VALID_MATRIX)

        self.assertEqual(VALID_MATRIX[0], result)

    def test_distribution_at_zero_returns_initial_vector(self):
        initial = [0.0, 1.0, 0.0, 0.0]

        self.assertEqual(initial, distribution_at(initial, VALID_MATRIX, 0))

    def test_distribution_at_returns_requested_horizons(self):
        initial = [1.0, 0.0, 0.0, 0.0]

        for horizon in (1, 3, 5, 10):
            with self.subTest(horizon=horizon):
                result = distribution_at(initial, VALID_MATRIX, horizon)
                self.assertAlmostEqual(1.0, sum(result))

    def test_identity_matrix_preserves_distribution(self):
        identity = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
        initial = [0.0, 0.0, 1.0, 0.0]

        self.assertEqual(initial, distribution_at(initial, identity, 10))

    def test_absorbing_state_keeps_all_probability(self):
        absorbing = [
            [0.5, 0.5, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
        initial = [0.0, 1.0, 0.0, 0.0]

        self.assertEqual(initial, distribution_at(initial, absorbing, 5))

    def test_trajectory_includes_initial_and_each_step_through_ten(self):
        result = trajectory([1.0, 0.0, 0.0, 0.0], VALID_MATRIX, 10)

        self.assertEqual(11, len(result))
        self.assertEqual([1.0, 0.0, 0.0, 0.0], result[0])

    def test_stationary_distribution_for_periodic_chain(self):
        cycle = [
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0, 0.0],
        ]

        result = stationary(cycle)

        self.assertIsNone(result.reason)
        self.assertEqual([0.25, 0.25, 0.25, 0.25], result.distribution)

    def test_stationary_reports_non_unique_solution(self):
        identity = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]

        result = stationary(identity)

        self.assertIsNone(result.distribution)
        self.assertTrue(result.reason)

    def test_distribution_rejects_negative_step_count(self):
        with self.assertRaises(ValueError):
            distribution_at([1.0, 0.0, 0.0, 0.0], VALID_MATRIX, -1)


if __name__ == "__main__":
    unittest.main()

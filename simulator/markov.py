import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


STATES = ("Fluido", "Moderado", "Congestionado", "Colapsado")
_MATRIX_SIZE = len(STATES)
_TOLERANCE = 1e-9


class MatrixError(ValueError):
    def __init__(self, message: str, invalid_rows: Sequence[int] = ()) -> None:
        super().__init__(message)
        self.invalid_rows = tuple(sorted(set(invalid_rows)))


@dataclass(frozen=True)
class StationaryResult:
    distribution: list[float] | None
    reason: str | None = None


def validate_matrix(matrix: Any, tolerance: float = 1e-9) -> None:
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("La tolerancia debe ser un número finito no negativo.")
    if (
        not isinstance(matrix, Sequence)
        or isinstance(matrix, (str, bytes))
        or len(matrix) != _MATRIX_SIZE
    ):
        raise MatrixError("La matriz de transición debe tener forma 4x4.")

    for row_index, row in enumerate(matrix):
        if (
            not isinstance(row, Sequence)
            or isinstance(row, (str, bytes))
            or len(row) != _MATRIX_SIZE
        ):
            raise MatrixError(
                f"La fila {row_index} debe tener exactamente 4 valores para formar una matriz 4x4.",
                (row_index,),
            )

    invalid_rows = []
    for row_index, row in enumerate(matrix):
        row_is_valid = True
        values = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                row_is_valid = False
                continue
            number = float(value)
            if not math.isfinite(number) or not 0 <= number <= 1:
                row_is_valid = False
                continue
            values.append(number)

        if not row_is_valid or len(values) != 4 or abs(sum(values) - 1.0) > tolerance:
            invalid_rows.append(row_index)

    if invalid_rows:
        raise MatrixError(
            "Cada fila de la matriz debe contener probabilidades entre 0 y 1 y sumar 1.",
            invalid_rows,
        )


def initial_vector(state_index: int) -> list[float]:
    if isinstance(state_index, bool) or not isinstance(state_index, int):
        raise ValueError("El índice del estado inicial debe ser un entero entre 0 y 3.")
    if not 0 <= state_index < _MATRIX_SIZE:
        raise ValueError("El índice del estado inicial debe ser un entero entre 0 y 3.")
    return [1.0 if index == state_index else 0.0 for index in range(_MATRIX_SIZE)]


def _validate_vector(vector: Any) -> list[float]:
    if (
        not isinstance(vector, Sequence)
        or isinstance(vector, (str, bytes))
        or len(vector) != _MATRIX_SIZE
    ):
        raise ValueError("El vector de distribución debe tener exactamente 4 valores.")

    values = []
    for value in vector:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("El vector debe contener probabilidades entre 0 y 1.")
        number = float(value)
        if not math.isfinite(number) or not 0 <= number <= 1:
            raise ValueError("El vector debe contener probabilidades entre 0 y 1.")
        values.append(number)

    if abs(sum(values) - 1.0) > _TOLERANCE:
        raise ValueError("El vector de distribución debe sumar 1.")
    return values


def _step_validated(vector: list[float], matrix: Sequence[Sequence[float]]) -> list[float]:
    return [
        sum(vector[row_index] * matrix[row_index][column_index] for row_index in range(_MATRIX_SIZE))
        for column_index in range(_MATRIX_SIZE)
    ]


def step(vector: Sequence[float], matrix: Sequence[Sequence[float]]) -> list[float]:
    validate_matrix(matrix)
    return _step_validated(_validate_vector(vector), matrix)


def _validate_step_count(step_count: int) -> None:
    if isinstance(step_count, bool) or not isinstance(step_count, int) or step_count < 0:
        raise ValueError("El número de pasos debe ser un entero no negativo.")


def distribution_at(
    vector: Sequence[float],
    matrix: Sequence[Sequence[float]],
    step_count: int,
) -> list[float]:
    _validate_step_count(step_count)
    distribution = _validate_vector(vector)
    validate_matrix(matrix)
    for _ in range(step_count):
        distribution = _step_validated(distribution, matrix)
    return distribution


def trajectory(
    vector: Sequence[float],
    matrix: Sequence[Sequence[float]],
    max_step: int,
) -> list[list[float]]:
    _validate_step_count(max_step)
    distribution = _validate_vector(vector)
    validate_matrix(matrix)
    distributions = [distribution.copy()]
    for _ in range(max_step):
        distribution = _step_validated(distribution, matrix)
        distributions.append(distribution)
    return distributions


def stationary(matrix: Sequence[Sequence[float]]) -> StationaryResult:
    validate_matrix(matrix)

    coefficients = [
        [
            float(matrix[variable][state]) - (1.0 if variable == state else 0.0)
            for variable in range(_MATRIX_SIZE)
        ]
        for state in range(_MATRIX_SIZE)
    ]
    coefficients[-1] = [1.0] * _MATRIX_SIZE
    right_hand_side = [0.0] * (_MATRIX_SIZE - 1) + [1.0]

    for column in range(_MATRIX_SIZE):
        pivot = max(
            range(column, _MATRIX_SIZE),
            key=lambda row: abs(coefficients[row][column]),
        )
        if abs(coefficients[pivot][column]) <= _TOLERANCE:
            return StationaryResult(
                None,
                "No se puede determinar una distribución estacionaria única.",
            )

        coefficients[column], coefficients[pivot] = coefficients[pivot], coefficients[column]
        right_hand_side[column], right_hand_side[pivot] = (
            right_hand_side[pivot],
            right_hand_side[column],
        )
        pivot_value = coefficients[column][column]
        coefficients[column] = [value / pivot_value for value in coefficients[column]]
        right_hand_side[column] /= pivot_value

        for row in range(_MATRIX_SIZE):
            if row == column:
                continue
            factor = coefficients[row][column]
            coefficients[row] = [
                value - factor * pivot_entry
                for value, pivot_entry in zip(coefficients[row], coefficients[column])
            ]
            right_hand_side[row] -= factor * right_hand_side[column]

    distribution = right_hand_side
    if any(value < -_TOLERANCE or value > 1.0 + _TOLERANCE for value in distribution):
        return StationaryResult(
            None,
            "La solución estacionaria numérica no es una distribución válida.",
        )

    distribution = [max(0.0, value) for value in distribution]
    total = sum(distribution)
    if not math.isfinite(total) or total <= 0:
        return StationaryResult(
            None,
            "La solución estacionaria numérica no es estable.",
        )
    distribution = [value / total for value in distribution]

    residual = _step_validated(distribution, matrix)
    if any(
        abs(residual[index] - distribution[index]) > _TOLERANCE
        for index in range(_MATRIX_SIZE)
    ):
        return StationaryResult(
            None,
            "La solución estacionaria numérica no es estable.",
        )
    return StationaryResult(distribution)

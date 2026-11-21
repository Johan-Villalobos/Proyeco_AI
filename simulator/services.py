from collections.abc import Sequence

from django.db.models import QuerySet

from simulator.markov import (
    STATES,
    distribution_at,
    initial_vector,
    trajectory,
    validate_matrix,
)
from simulator.models import Scenario, Simulation


# Each Markov step represents one 30-minute block.
HORIZON_MINUTES = {1: 30, 3: 90, 5: 150, 10: 300}
HORIZONS = tuple(HORIZON_MINUTES)
MAX_HISTORY = 20


def get_scenarios() -> QuerySet[Scenario]:
    return Scenario.objects.order_by("name")


def scenario_for_matrix(
    scenario_id: int | None,
    matrix: Sequence[Sequence[float]],
) -> Scenario | None:
    validate_matrix(matrix)
    if scenario_id is None:
        return None
    scenario = Scenario.objects.get(pk=scenario_id)
    if scenario.matrix == [list(row) for row in matrix]:
        return scenario
    return None


def run_simulation(
    matrix: Sequence[Sequence[float]],
    initial_state: int,
    steps: Sequence[int] = HORIZONS,
) -> dict[str, object]:
    requested_steps = tuple(steps)
    if requested_steps != HORIZONS:
        raise ValueError(f"Los horizontes admitidos son {HORIZONS}.")

    validate_matrix(matrix)
    starting_vector = initial_vector(initial_state)
    results = {
        str(horizon): distribution_at(starting_vector, matrix, horizon)
        for horizon in HORIZONS
    }
    return {
        "results": results,
        "trajectory": trajectory(starting_vector, matrix, max(HORIZONS)),
        "interpretation": interpret_results(results),
    }


def interpret_results(results: dict[str, object]) -> str:
    final_distribution = results[str(max(HORIZONS))]
    if not isinstance(final_distribution, list) or len(final_distribution) != len(HORIZONS):
        raise ValueError("Los resultados no contienen una distribución final válida.")
    most_likely_state = max(range(len(final_distribution)), key=final_distribution.__getitem__)
    probability = float(final_distribution[most_likely_state])
    return (
        f"A los {max(HORIZONS)} pasos (5 horas), el estado más probable es "
        f"{STATES[most_likely_state]} "
        f"({probability:.1%})."
    )


def save_simulation(
    scenario: Scenario | None,
    initial_state: int,
    matrix: Sequence[Sequence[float]],
    results: dict[str, object],
) -> Simulation:
    validate_matrix(matrix)
    initial_vector(initial_state)
    simulation = Simulation(
        scenario=scenario,
        initial_state=initial_state,
        matrix=matrix,
        results=results,
    )
    simulation.full_clean()
    simulation.save()
    return simulation


def recent_history(limit: int = MAX_HISTORY) -> QuerySet[Simulation]:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("El límite del historial debe ser un entero positivo.")
    return Simulation.objects.order_by("-created_at", "-pk")[: min(limit, MAX_HISTORY)]

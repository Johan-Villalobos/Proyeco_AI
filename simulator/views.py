import json
from json import JSONDecodeError

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from simulator import services
from simulator.markov import MatrixError, STATES
from simulator.models import Scenario


class RequestDataError(ValueError):
    pass


def _json_payload(request: HttpRequest) -> dict[str, object]:
    if request.content_type != "application/json":
        raise RequestDataError("El contenido de la solicitud debe ser JSON.")
    try:
        payload = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError) as error:
        raise RequestDataError("El cuerpo de la solicitud no contiene JSON válido.") from error
    if not isinstance(payload, dict):
        raise RequestDataError("El cuerpo JSON debe ser un objeto.")
    return payload


def _error_response(error: Exception) -> JsonResponse:
    invalid_rows = list(error.invalid_rows) if isinstance(error, MatrixError) else []
    return JsonResponse(
        {"error": _error_message(error), "invalid_rows": invalid_rows},
        status=400,
    )


def _error_message(error: Exception) -> str:
    message = str(error)
    if isinstance(error, MatrixError) and error.invalid_rows:
        rows = ", ".join(str(row) for row in error.invalid_rows)
        message = f"{message} Filas inválidas: {rows}."
    return message


class IndexView(TemplateView):
    template_name = "simulator/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        scenarios = list(services.get_scenarios())
        default_scenario = scenarios[0] if scenarios else None
        matrix_rows = []
        if default_scenario:
            for row_index, row in enumerate(default_scenario.matrix):
                matrix_rows.append(
                    {
                        "index": row_index,
                        "label": STATES[row_index],
                        "cells": [
                            {
                                "row": row_index,
                                "column": column_index,
                                "row_label": STATES[row_index],
                                "column_label": STATES[column_index],
                                "value": format(value, ".15g"),
                            }
                            for column_index, value in enumerate(row)
                        ],
                    }
                )
        context.update(
            {
                "scenarios": scenarios,
                "states": STATES,
                "default_state": 0,
                "default_scenario": default_scenario,
                "initial_matrix": default_scenario.matrix if default_scenario else None,
                "horizons": services.HORIZONS,
                "horizon_minutes": services.HORIZON_MINUTES,
                "horizon_rows": [
                    {
                        "steps": steps,
                        "time_label": (
                            f"{minutes} min"
                            if minutes < 60
                            else f"{minutes / 60:g} h"
                        ),
                    }
                    for steps, minutes in services.HORIZON_MINUTES.items()
                ],
                "matrix_rows": matrix_rows,
            }
        )
        return context


@require_GET
def scenarios_api(request: HttpRequest) -> JsonResponse:
    scenarios = [
        {
            "id": scenario.pk,
            "name": scenario.name,
            "slug": scenario.slug,
            "description": scenario.description,
            "matrix": scenario.matrix,
            "is_preset": scenario.is_preset,
        }
        for scenario in services.get_scenarios()
    ]
    return JsonResponse({"scenarios": scenarios})


@require_POST
def validate_api(request: HttpRequest) -> JsonResponse:
    try:
        payload = _json_payload(request)
        services.validate_matrix(payload.get("matrix"))
    except (RequestDataError, MatrixError) as error:
        response = {
            "valid": False,
            "invalid_rows": list(error.invalid_rows)
            if isinstance(error, MatrixError)
            else [],
            "error": _error_message(error),
        }
        return JsonResponse(response, status=400)
    return JsonResponse({"valid": True, "invalid_rows": []})


@require_POST
def simulate_api(request: HttpRequest) -> JsonResponse:
    try:
        payload = _json_payload(request)
        matrix = payload.get("matrix")
        initial_state = payload.get("initial_state")
        if isinstance(initial_state, bool) or not isinstance(initial_state, int):
            raise RequestDataError("El estado inicial debe ser un entero entre 0 y 3.")

        scenario_id = payload.get("scenario_id")
        if scenario_id is not None and (
            isinstance(scenario_id, bool)
            or not isinstance(scenario_id, int)
            or scenario_id <= 0
        ):
            raise RequestDataError("El identificador del escenario debe ser un entero positivo.")

        result = services.run_simulation(matrix, initial_state)
        scenario = services.scenario_for_matrix(scenario_id, matrix)
        services.save_simulation(
            scenario=scenario,
            initial_state=initial_state,
            matrix=matrix,
            results=result["results"],
        )
    except (RequestDataError, MatrixError, ValueError) as error:
        return _error_response(error)
    except Scenario.DoesNotExist:
        return _error_response(RequestDataError("El escenario seleccionado no existe."))

    return JsonResponse(
        {
            "results": result["results"],
            "trajectory": result["trajectory"],
            "interpretation": result["interpretation"],
        }
    )


@require_GET
def history_api(request: HttpRequest) -> JsonResponse:
    simulations = [
        {
            "id": simulation.pk,
            "scenario_id": simulation.scenario_id,
            "initial_state": simulation.initial_state,
            "matrix": simulation.matrix,
            "results": simulation.results,
            "created_at": simulation.created_at.isoformat(),
        }
        for simulation in services.recent_history()
    ]
    return JsonResponse({"simulations": simulations})

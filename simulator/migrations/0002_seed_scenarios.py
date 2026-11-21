from django.db import migrations


SCENARIOS = [
    {
        "name": "Hora pico mañana",
        "slug": "hora-pico-manana",
        "description": (
            "Alta demanda vehicular; el tráfico tiende a congestionarse y la "
            "recuperación es lenta. Valores ilustrativos didácticos, no datos "
            "reales medidos."
        ),
        "matrix": [
            [0.50, 0.35, 0.13, 0.02],
            [0.15, 0.45, 0.35, 0.05],
            [0.05, 0.25, 0.55, 0.15],
            [0.00, 0.10, 0.40, 0.50],
        ],
    },
    {
        "name": "Día lluvioso",
        "slug": "dia-lluvioso",
        "description": (
            "La lluvia reduce la velocidad y aumenta el riesgo de accidentes; "
            "hay mayor probabilidad de colapso y la recuperación es más lenta. "
            "Valores ilustrativos didácticos, no datos reales medidos."
        ),
        "matrix": [
            [0.55, 0.30, 0.12, 0.03],
            [0.20, 0.40, 0.33, 0.07],
            [0.05, 0.25, 0.52, 0.18],
            [0.00, 0.08, 0.37, 0.55],
        ],
    },
    {
        "name": "Domingo/Festivo",
        "slug": "domingo-festivo",
        "description": (
            "Baja demanda; el tráfico permanece mayormente fluido y se recupera "
            "rápido de cualquier congestión. Valores ilustrativos didácticos, "
            "no datos reales medidos."
        ),
        "matrix": [
            [0.85, 0.12, 0.02, 0.01],
            [0.45, 0.40, 0.12, 0.03],
            [0.20, 0.40, 0.35, 0.05],
            [0.10, 0.30, 0.35, 0.25],
        ],
    },
]


def seed_scenarios(apps, schema_editor):
    scenario_model = apps.get_model("simulator", "Scenario")
    database = schema_editor.connection.alias
    for data in SCENARIOS:
        scenario_model.objects.using(database).update_or_create(
            slug=data["slug"],
            defaults={**data, "is_preset": True},
        )


def unseed_scenarios(apps, schema_editor):
    scenario_model = apps.get_model("simulator", "Scenario")
    database = schema_editor.connection.alias
    scenario_model.objects.using(database).filter(
        slug__in=[scenario["slug"] for scenario in SCENARIOS],
        is_preset=True,
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("simulator", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_scenarios, unseed_scenarios),
    ]

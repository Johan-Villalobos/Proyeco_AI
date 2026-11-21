from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from simulator.markov import MatrixError, validate_matrix


class Scenario(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    matrix = models.JSONField()
    is_preset = models.BooleanField(default=False)

    def clean(self) -> None:
        super().clean()
        try:
            validate_matrix(self.matrix)
        except MatrixError as error:
            message = str(error)
            if error.invalid_rows:
                rows = ", ".join(str(row) for row in error.invalid_rows)
                message = f"{message} Filas inválidas: {rows}."
            raise ValidationError({"matrix": message}) from error

    def __str__(self) -> str:
        return self.name


class Simulation(models.Model):
    scenario = models.ForeignKey(
        Scenario,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="simulations",
    )
    initial_state = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(3)]
    )
    matrix = models.JSONField()
    results = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

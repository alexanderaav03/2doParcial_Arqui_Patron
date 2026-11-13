from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas.detalle_rutina import DetalleRutinaCreate


class ParametrizacionInvalida(Exception):
    """La estrategia no puede calcular parámetros con los datos disponibles."""


@dataclass(frozen=True)
class ParametrosEntrenamiento:
    """Resultado común de todas las estrategias (lo que se guarda en DetalleRutina)."""

    series: int
    repeticiones: int
    sesiones_por_semana: int
    peso: float
    descanso_serie: str
    descanso_ejercicio: str
    rpe: int


class EstrategiaParametrizacion(ABC):
    """<<interface>> Strategy: declara el método que usa el contexto."""

    @abstractmethod
    def calcular(self, solicitud: DetalleRutinaCreate) -> ParametrosEntrenamiento:
        """Devuelve los parámetros de entrenamiento para el nuevo detalle."""

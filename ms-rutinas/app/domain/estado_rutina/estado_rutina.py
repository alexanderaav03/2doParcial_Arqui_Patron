from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.estado_rutina.rutina_contexto import RutinaContexto
    from app.models.detalle_rutina import DetalleRutina
    from app.models.registro_progreso import RegistroProgreso
    from app.schemas.registro_progreso import RegistroProgresoCreate


class OperacionNoPermitida(Exception):
    """La operación no está permitida en el estado actual de la rutina."""


class EstadoRutina(ABC):
    """<<interface>> Estado: métodos que tienen sentido en TODOS los estados.

    Guarda una referencia inversa al contexto para poder leer la rutina y
    provocar transiciones (cambiar_estado).
    """

    nombre: str = ""

    def __init__(self, contexto: RutinaContexto) -> None:
        self.contexto = contexto

    @abstractmethod
    def actualizar(self, hoy: date) -> None:
        """Revisa las fechas y, si corresponde, pasa al siguiente estado."""

    @abstractmethod
    def registrar_progreso(self, detalle: DetalleRutina, datos: RegistroProgresoCreate) -> RegistroProgreso:
        """CU07: guarda el resultado real del cliente (solo En curso lo permite)."""

    @abstractmethod
    def validar_edicion(self) -> None:
        """CU03/CU04: ¿se puede modificar la rutina o su detalle?"""

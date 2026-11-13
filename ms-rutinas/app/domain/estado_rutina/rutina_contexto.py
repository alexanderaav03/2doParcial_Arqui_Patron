from __future__ import annotations

from datetime import date

from app.domain.estado_rutina.estado_rutina import EstadoRutina
from app.domain.estado_rutina.estados import Programada
from app.models.detalle_rutina import DetalleRutina
from app.models.registro_progreso import RegistroProgreso
from app.models.rutina import Rutina
from app.repositories.registro_progreso_repository import RegistroProgresoRepository
from app.schemas.registro_progreso import RegistroProgresoCreate


class RutinaContexto:
    """Contexto del patrón State.

    Envuelve la entidad Rutina, guarda el estado actual y le DELEGA el
    trabajo que depende del estado. No tiene ni un if sobre el estado.
    """

    def __init__(self, rutina: Rutina, hoy: date, registro_repo: RegistroProgresoRepository | None = None) -> None:
        self.rutina = rutina
        self.registro_repo = registro_repo
        self.estado: EstadoRutina = Programada(self)  # estado inicial del ciclo de vida
        self.estado.actualizar(hoy)  # las propias clases de estado deciden las transiciones

    def cambiar_estado(self, nuevo: EstadoRutina) -> None:
        self.estado = nuevo

    def registrar_progreso(self, detalle: DetalleRutina, datos: RegistroProgresoCreate) -> RegistroProgreso:
        return self.estado.registrar_progreso(detalle, datos)

    def validar_edicion(self) -> None:
        self.estado.validar_edicion()

    @property
    def nombre_estado(self) -> str:
        return self.estado.nombre

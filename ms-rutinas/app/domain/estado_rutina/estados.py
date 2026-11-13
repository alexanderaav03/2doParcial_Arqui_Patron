from __future__ import annotations

from datetime import date

from app.domain.estado_rutina.estado_rutina import EstadoRutina, OperacionNoPermitida
from app.models.registro_progreso import RegistroProgreso


class Programada(EstadoRutina):
    """Estado concreto: hoy < fecha_inicio."""

    nombre = "programada"

    def actualizar(self, hoy: date) -> None:
        if hoy >= self.contexto.rutina.fecha_inicio:
            self.contexto.cambiar_estado(EnCurso(self.contexto))
            self.contexto.estado.actualizar(hoy)  # por si también ya terminó

    def registrar_progreso(self, detalle, datos):
        raise OperacionNoPermitida(
            f"La rutina aún no inicia (empieza el {self.contexto.rutina.fecha_inicio}); no se puede registrar progreso"
        )

    def validar_edicion(self) -> None:
        return None  # se puede editar libremente


class EnCurso(EstadoRutina):
    """Estado concreto: fecha_inicio <= hoy <= fecha_fin."""

    nombre = "en_curso"

    def actualizar(self, hoy: date) -> None:
        if hoy > self.contexto.rutina.fecha_fin:
            self.contexto.cambiar_estado(Finalizada(self.contexto))

    def registrar_progreso(self, detalle, datos):
        registro = RegistroProgreso(
            detalle_rutina_id=detalle.id,
            series_realizadas=datos.series_realizadas,
            repeticiones_realizadas=datos.repeticiones_realizadas,
            peso_realizado=datos.peso_realizado,
            nota=datos.nota,
        )
        return self.contexto.registro_repo.create(registro)

    def validar_edicion(self) -> None:
        return None  # el instructor puede ajustar cargas mientras dura


class Finalizada(EstadoRutina):
    """Estado concreto (final): hoy > fecha_fin. Solo lectura."""

    nombre = "finalizada"

    def actualizar(self, hoy: date) -> None:
        return None  # estado final, no hay transición

    def registrar_progreso(self, detalle, datos):
        raise OperacionNoPermitida(
            f"La rutina finalizó el {self.contexto.rutina.fecha_fin}; ya no admite registros de progreso"
        )

    def validar_edicion(self) -> None:
        raise OperacionNoPermitida("La rutina está finalizada; solo se puede consultar")

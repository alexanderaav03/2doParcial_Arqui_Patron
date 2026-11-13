from app.schemas.detalle_rutina import DetalleRutinaCreate
from app.services.parametrizacion.estrategia_parametrizacion import (
    EstrategiaParametrizacion,
    ParametrizacionInvalida,
    ParametrosEntrenamiento,
)

CAMPOS = ("series", "repeticiones", "peso", "descanso_serie", "descanso_ejercicio", "rpe")


class ParametrosManuales(EstrategiaParametrizacion):
    """Estrategia concreta 1: el instructor escribe todos los valores (comportamiento del 1er parcial)."""

    def calcular(self, solicitud: DetalleRutinaCreate) -> ParametrosEntrenamiento:
        faltantes = [c for c in CAMPOS if getattr(solicitud, c) is None]
        if faltantes:
            raise ParametrizacionInvalida(f"Modo manual: faltan los campos {', '.join(faltantes)}")
        return ParametrosEntrenamiento(
            series=solicitud.series,
            repeticiones=solicitud.repeticiones,
            sesiones_por_semana=solicitud.sesiones_por_semana,
            peso=solicitud.peso,
            descanso_serie=solicitud.descanso_serie,
            descanso_ejercicio=solicitud.descanso_ejercicio,
            rpe=solicitud.rpe,
        )

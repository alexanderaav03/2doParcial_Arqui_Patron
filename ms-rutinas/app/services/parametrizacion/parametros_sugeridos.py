from typing import Any

from app.schemas.detalle_rutina import DetalleRutinaCreate
from app.services.parametrizacion.estrategia_parametrizacion import (
    EstrategiaParametrizacion,
    ParametrizacionInvalida,
    ParametrosEntrenamiento,
)

SUGERIDOS = (
    "series_sugeridas",
    "repeticiones_sugeridas",
    "peso_sugerido",
    "descanso_serie_sugerido",
    "descanso_ejercicio_sugerido",
    "rpe_sugerido",
)


class ParametrosSugeridos(EstrategiaParametrizacion):
    """Estrategia concreta 2: copia los valores sugeridos del banco de ejercicios.

    `ejercicio` es el JSON que devuelve ms-ejercicios (GET /api/ejercicios/{id}).
    """

    def __init__(self, ejercicio: dict[str, Any]) -> None:
        self._ejercicio = ejercicio

    def calcular(self, solicitud: DetalleRutinaCreate) -> ParametrosEntrenamiento:
        faltantes = [c for c in SUGERIDOS if self._ejercicio.get(c) is None]
        if faltantes:
            raise ParametrizacionInvalida(
                f"El ejercicio '{self._ejercicio.get('nombre')}' no tiene valores sugeridos completos"
            )
        e = self._ejercicio
        return ParametrosEntrenamiento(
            series=e["series_sugeridas"],
            repeticiones=e["repeticiones_sugeridas"],
            sesiones_por_semana=solicitud.sesiones_por_semana,
            peso=float(e["peso_sugerido"]),
            descanso_serie=str(e["descanso_serie_sugerido"]),
            descanso_ejercicio=str(e["descanso_ejercicio_sugerido"]),
            rpe=e["rpe_sugerido"],
        )


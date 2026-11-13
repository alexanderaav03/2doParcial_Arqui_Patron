from app.schemas.detalle_rutina import DetalleRutinaCreate
from app.services.parametrizacion.estrategia_parametrizacion import (
    EstrategiaParametrizacion,
    ParametrosEntrenamiento,
)


class ParametrizadorDetalle:
    """Contexto del patrón Strategy.

    Guarda una referencia a la estrategia y solo la conoce por su interfaz.
    No sabe CÓMO se calculan los parámetros.
    """

    def __init__(self, estrategia: EstrategiaParametrizacion) -> None:
        self._estrategia = estrategia

    def set_estrategia(self, estrategia: EstrategiaParametrizacion) -> None:
        self._estrategia = estrategia

    def parametrizar(self, solicitud: DetalleRutinaCreate) -> ParametrosEntrenamiento:
        return self._estrategia.calcular(solicitud)

from app.repositories.registro_progreso_repository import RegistroProgresoRepository
from app.schemas.detalle_rutina import DetalleRutinaCreate
from app.services.parametrizacion.estrategia_parametrizacion import (
    EstrategiaParametrizacion,
    ParametrizacionInvalida,
    ParametrosEntrenamiento,
)

INCREMENTO = 0.05  # +5 % de carga si el cliente cumplió lo prescrito


def _redondear_medio_kilo(valor: float) -> float:
    return round(valor * 2) / 2


class ProgresionCarga(EstrategiaParametrizacion):
    """Estrategia concreta 3: sobrecarga progresiva según el último progreso del cliente.

    Busca el último RegistroProgreso del cliente en ESTE ejercicio (en cualquier
    rutina anterior). Si cumplió las series y repeticiones prescritas, sube la
    carga 5 %; si no, mantiene el peso que realmente levantó.
    """

    def __init__(self, registro_repo: RegistroProgresoRepository, cliente_id: int) -> None:
        self._registro_repo = registro_repo
        self._cliente_id = cliente_id

    def calcular(self, solicitud: DetalleRutinaCreate) -> ParametrosEntrenamiento:
        ultimo = self._registro_repo.ultimo_de_cliente_y_ejercicio(self._cliente_id, solicitud.ejercicio_id)
        if ultimo is None:
            raise ParametrizacionInvalida(
                "El cliente no tiene progreso previo en este ejercicio; use el modo manual o sugeridos"
            )
        registro, detalle_anterior = ultimo
        cumplio = (
            registro.series_realizadas >= detalle_anterior.series
            and registro.repeticiones_realizadas >= detalle_anterior.repeticiones
        )
        peso = registro.peso_realizado * (1 + INCREMENTO) if cumplio else registro.peso_realizado
        return ParametrosEntrenamiento(
            series=detalle_anterior.series,
            repeticiones=detalle_anterior.repeticiones,
            sesiones_por_semana=solicitud.sesiones_por_semana,
            peso=_redondear_medio_kilo(peso),
            descanso_serie=detalle_anterior.descanso_serie,
            descanso_ejercicio=detalle_anterior.descanso_ejercicio,
            rpe=detalle_anterior.rpe,
        )

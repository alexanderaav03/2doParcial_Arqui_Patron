from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.clients.ejercicios_client import ejercicios_client
from app.dependencies import CurrentUser
from app.domain.estado_rutina import OperacionNoPermitida, RutinaContexto, hoy
from app.models.detalle_rutina import DetalleRutina
from app.models.rutina import Rutina
from app.repositories.detalle_rutina_repository import DetalleRutinaRepository
from app.repositories.registro_progreso_repository import RegistroProgresoRepository
from app.schemas.detalle_rutina import (
    DetalleRutinaCreate,
    DetalleRutinaResponse,
    DetalleRutinaUpdate,
    ModoParametrizacion,
)
from app.services.parametrizacion import (
    EstrategiaParametrizacion,
    ParametrizacionInvalida,
    ParametrizadorDetalle,
    ParametrosManuales,
    ParametrosSugeridos,
    ProgresionCarga,
)
from app.services.rutina_service import RutinaService


class DetalleService:
    def __init__(self, db: Session) -> None:
        self.detalle_repo = DetalleRutinaRepository(db)
        self.registro_repo = RegistroProgresoRepository(db)
        self.rutina_service = RutinaService(db)

    def _crear_estrategia(
        self, modo: ModoParametrizacion, ejercicio: dict, rutina: Rutina
    ) -> EstrategiaParametrizacion:
        """Cliente del patrón Strategy: elige la estrategia concreta según el
        modo pedido. Solo ELIGE; el algoritmo vive en cada clase."""
        if modo is ModoParametrizacion.SUGERIDOS:
            return ParametrosSugeridos(ejercicio)
        if modo is ModoParametrizacion.PROGRESION:
            return ProgresionCarga(self.registro_repo, rutina.cliente_id)
        return ParametrosManuales()

    def _validar_editable(self, rutina: Rutina) -> None:
        """Patrón State reutilizado: una rutina Finalizada no se modifica."""
        try:
            RutinaContexto(rutina, hoy()).validar_edicion()
        except OperacionNoPermitida as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from None

    def list_by_rutina(self, rutina_id: int, current_user: CurrentUser) -> list[DetalleRutinaResponse]:
        rutina = self.rutina_service.get_rutina_or_404(rutina_id)
        self.rutina_service._ensure_rutina_access(rutina, current_user)
        detalles = self.detalle_repo.list_by_rutina(rutina_id)
        return [DetalleRutinaResponse.from_model(d) for d in detalles]

    async def create(
        self,
        rutina_id: int,
        data: DetalleRutinaCreate,
        bearer_token: str,
    ) -> DetalleRutinaResponse:
        rutina = self.rutina_service.get_rutina_or_404(rutina_id)
        await self.rutina_service.assert_instructor_dueno(rutina, bearer_token)
        self._validar_editable(rutina)
        ejercicio = await ejercicios_client.validate_ejercicio(data.ejercicio_id, bearer_token)

        if self.detalle_repo.exists_by_rutina_y_ejercicio(rutina_id, data.ejercicio_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este ejercicio ya está en la rutina",
            )

        # --- Patrón Strategy ---
        parametrizador = ParametrizadorDetalle(self._crear_estrategia(data.modo, ejercicio, rutina))
        try:
            p = parametrizador.parametrizar(data)
        except ParametrizacionInvalida as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from None

        detalle = DetalleRutina(
            rutina_id=rutina_id,
            ejercicio_id=data.ejercicio_id,
            repeticiones=p.repeticiones,
            series=p.series,
            sesiones_por_semana=p.sesiones_por_semana,
            peso=p.peso,
            descanso_serie=p.descanso_serie,
            descanso_ejercicio=p.descanso_ejercicio,
            rpe=p.rpe,
        )
        created = self.detalle_repo.create(detalle)
        return DetalleRutinaResponse.from_model(created)

    async def update(
        self,
        rutina_id: int,
        detalle_id: int,
        data: DetalleRutinaUpdate,
        bearer_token: str,
    ) -> DetalleRutinaResponse:
        rutina = self.rutina_service.get_rutina_or_404(rutina_id)
        await self.rutina_service.assert_instructor_dueno(rutina, bearer_token)
        self._validar_editable(rutina)

        detalle = self.detalle_repo.get_by_id(detalle_id)
        if detalle is None or detalle.rutina_id != rutina_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detalle no encontrado",
            )

        cambios = data.model_dump(exclude_unset=True)
        actualizado = self.detalle_repo.update(detalle, cambios)
        return DetalleRutinaResponse.from_model(actualizado)

    async def delete(self, rutina_id: int, detalle_id: int, bearer_token: str) -> None:
        rutina = self.rutina_service.get_rutina_or_404(rutina_id)
        await self.rutina_service.assert_instructor_dueno(rutina, bearer_token)
        self._validar_editable(rutina)

        detalle = self.detalle_repo.get_by_id(detalle_id)
        if detalle is None or detalle.rutina_id != rutina_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detalle no encontrado",
            )

        self.detalle_repo.delete(detalle)

    def existe_ejercicio(self, ejercicio_id: int) -> bool:
        """True si el ejercicio está referenciado en algún DetalleRutina, de
        cualquier rutina/cliente -no filtra por instructor-. La usa
        ms-ejercicios antes de permitir borrar un ejercicio del banco."""
        return self.detalle_repo.exists_by_ejercicio(ejercicio_id)

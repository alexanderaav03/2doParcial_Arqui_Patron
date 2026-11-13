from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import CurrentUser
from app.domain.estado_rutina import OperacionNoPermitida, RutinaContexto, hoy
from app.models.detalle_rutina import DetalleRutina
from app.models.rutina import Rutina
from app.repositories.detalle_rutina_repository import DetalleRutinaRepository
from app.repositories.registro_progreso_repository import RegistroProgresoRepository
from app.schemas.registro_progreso import RegistroProgresoCreate, RegistroProgresoResponse
from app.services.rutina_service import RutinaService


class ProgresoService:
    def __init__(self, db: Session) -> None:
        self.registro_repo = RegistroProgresoRepository(db)
        self.detalle_repo = DetalleRutinaRepository(db)
        self.rutina_service = RutinaService(db)

    def _get_rutina_y_detalle(self, rutina_id: int, detalle_id: int) -> tuple[Rutina, DetalleRutina]:
        rutina = self.rutina_service.get_rutina_or_404(rutina_id)
        detalle = self.detalle_repo.get_by_id(detalle_id)
        if detalle is None or detalle.rutina_id != rutina_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detalle no encontrado",
            )
        return rutina, detalle

    def crear_registro(
        self,
        rutina_id: int,
        detalle_id: int,
        data: RegistroProgresoCreate,
        current_user: CurrentUser,
    ) -> RegistroProgresoResponse:
        rutina, detalle = self._get_rutina_y_detalle(rutina_id, detalle_id)

        # Mismo chequeo de ownership de cliente que ya usan list_by_cliente/
        # get_by_id en RutinaService (403, no 404: acá sí sabemos que el
        # cliente autenticado existe, solo no es dueño de esta rutina).
        self.rutina_service._ensure_rutina_access(rutina, current_user)

        # --- Patrón State: el estado de la rutina decide si se permite ---
        contexto = RutinaContexto(rutina, hoy(), self.registro_repo)
        try:
            created = contexto.registrar_progreso(detalle, data)
        except OperacionNoPermitida as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from None
        return RegistroProgresoResponse.model_validate(created)

    async def listar_registros(
        self,
        rutina_id: int,
        detalle_id: int,
        current_user: CurrentUser,
        bearer_token: str,
    ) -> list[RegistroProgresoResponse]:
        rutina, detalle = self._get_rutina_y_detalle(rutina_id, detalle_id)

        if current_user.rol == "instructor":
            # Cross-servicio contra ms-ejercicios, mismo patrón que editar/
            # eliminar rutina y detalles.
            await self.rutina_service.assert_instructor_dueno(rutina, bearer_token)
        else:
            self.rutina_service._ensure_rutina_access(rutina, current_user)

        registros = self.registro_repo.list_by_detalle(detalle.id)
        return [RegistroProgresoResponse.model_validate(r) for r in registros]

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.detalle_rutina import DetalleRutina
from app.models.registro_progreso import RegistroProgreso
from app.models.rutina import Rutina


class RegistroProgresoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_detalle(self, detalle_rutina_id: int) -> list[RegistroProgreso]:
        stmt = (
            select(RegistroProgreso)
            .where(RegistroProgreso.detalle_rutina_id == detalle_rutina_id)
            .order_by(RegistroProgreso.fecha.desc())
        )
        return list(self.db.scalars(stmt).all())

    def create(self, registro: RegistroProgreso) -> RegistroProgreso:
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def exists_by_rutina(self, rutina_id: int) -> bool:
        """True si algún DetalleRutina de esta rutina tiene al menos 1
        RegistroProgreso -se consulta local, ambas tablas viven en esta
        misma base-."""
        stmt = (
            select(RegistroProgreso.id)
            .join(DetalleRutina, RegistroProgreso.detalle_rutina_id == DetalleRutina.id)
            .where(DetalleRutina.rutina_id == rutina_id)
            .limit(1)
        )
        return self.db.scalars(stmt).first() is not None

    def ultimo_de_cliente_y_ejercicio(
        self, cliente_id: int, ejercicio_id: int
    ) -> tuple[RegistroProgreso, DetalleRutina] | None:
        """Último registro del cliente en ese ejercicio, en cualquiera de sus
        rutinas, junto con el detalle que se le había prescrito (lo usa la
        estrategia ProgresionCarga)."""
        stmt = (
            select(RegistroProgreso, DetalleRutina)
            .join(DetalleRutina, RegistroProgreso.detalle_rutina_id == DetalleRutina.id)
            .join(Rutina, DetalleRutina.rutina_id == Rutina.id)
            .where(Rutina.cliente_id == cliente_id, DetalleRutina.ejercicio_id == ejercicio_id)
            .order_by(RegistroProgreso.fecha.desc(), RegistroProgreso.id.desc())
            .limit(1)
        )
        fila = self.db.execute(stmt).first()
        return (fila[0], fila[1]) if fila else None

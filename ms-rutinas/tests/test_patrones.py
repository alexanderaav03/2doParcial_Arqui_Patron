"""Pruebas de los patrones Strategy (CU04) y State (CU07).

Ejecutar desde ms-rutinas:  DATABASE_URL=sqlite:// python -m pytest -q
"""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.domain.estado_rutina import EnCurso, Finalizada, OperacionNoPermitida, Programada, RutinaContexto
from app.models import DetalleRutina, RegistroProgreso, Rutina
from app.repositories.registro_progreso_repository import RegistroProgresoRepository
from app.schemas.detalle_rutina import DetalleRutinaCreate
from app.schemas.registro_progreso import RegistroProgresoCreate
from app.services.parametrizacion import (
    ParametrizacionInvalida,
    ParametrizadorDetalle,
    ParametrosManuales,
    ParametrosSugeridos,
    ProgresionCarga,
)

HOY = date(2026, 11, 10)


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sesion = sessionmaker(bind=engine)()
    yield sesion
    sesion.close()


def _rutina(db, inicio, fin, cliente_id=1):
    r = Rutina(cliente_id=cliente_id, nombre="Rutina", fecha_inicio=inicio, fecha_fin=fin)
    db.add(r)
    db.commit()
    return r


def _detalle(db, rutina, ejercicio_id=7, series=4, reps=10, peso=40.0):
    d = DetalleRutina(
        rutina_id=rutina.id, ejercicio_id=ejercicio_id, repeticiones=reps, series=series,
        sesiones_por_semana=3, peso=peso, descanso_serie="90 s", descanso_ejercicio="2 min", rpe=8,
    )
    db.add(d)
    db.commit()
    return d


# ---------------- STRATEGY (CU04) ----------------

def test_manual_usa_lo_que_escribe_el_instructor():
    s = DetalleRutinaCreate(ejercicio_id=7, sesiones_por_semana=3, series=3, repeticiones=12,
                            peso=20, descanso_serie="1 min", descanso_ejercicio="2 min", rpe=6)
    p = ParametrizadorDetalle(ParametrosManuales()).parametrizar(s)
    assert (p.series, p.repeticiones, p.peso) == (3, 12, 20)


def test_manual_sin_campos_falla():
    with pytest.raises(ParametrizacionInvalida):
        ParametrosManuales().calcular(DetalleRutinaCreate(ejercicio_id=7, sesiones_por_semana=3))


def test_sugeridos_copia_el_banco():
    ejercicio = {"nombre": "Sentadilla", "series_sugeridas": 4, "repeticiones_sugeridas": 8, "peso_sugerido": 60,
                 "descanso_serie_sugerido": "2 min", "descanso_ejercicio_sugerido": "3 min", "rpe_sugerido": 8}
    s = DetalleRutinaCreate(ejercicio_id=7, modo="sugeridos", sesiones_por_semana=2)
    p = ParametrizadorDetalle(ParametrosSugeridos(ejercicio)).parametrizar(s)
    assert (p.series, p.repeticiones, p.peso, p.sesiones_por_semana) == (4, 8, 60.0, 2)


def test_progresion_sube_5_por_ciento_si_cumplio(db):
    vieja = _rutina(db, HOY - timedelta(days=40), HOY - timedelta(days=10))
    d = _detalle(db, vieja, series=4, reps=10, peso=40)
    db.add(RegistroProgreso(detalle_rutina_id=d.id, fecha=datetime(2026, 10, 25), series_realizadas=4,
                            repeticiones_realizadas=10, peso_realizado=40))
    db.commit()
    s = DetalleRutinaCreate(ejercicio_id=7, modo="progresion", sesiones_por_semana=3)
    contexto = ParametrizadorDetalle(ParametrosManuales())
    contexto.set_estrategia(ProgresionCarga(RegistroProgresoRepository(db), cliente_id=1))  # cambio en ejecución
    p = contexto.parametrizar(s)
    assert p.peso == 42.0 and p.series == 4


def test_progresion_mantiene_si_no_cumplio(db):
    vieja = _rutina(db, HOY - timedelta(days=40), HOY - timedelta(days=10))
    d = _detalle(db, vieja, series=4, reps=10, peso=40)
    db.add(RegistroProgreso(detalle_rutina_id=d.id, series_realizadas=4, repeticiones_realizadas=7, peso_realizado=37.5))
    db.commit()
    p = ProgresionCarga(RegistroProgresoRepository(db), 1).calcular(
        DetalleRutinaCreate(ejercicio_id=7, modo="progresion", sesiones_por_semana=3))
    assert p.peso == 37.5


def test_progresion_sin_historial_falla(db):
    with pytest.raises(ParametrizacionInvalida):
        ProgresionCarga(RegistroProgresoRepository(db), 1).calcular(
            DetalleRutinaCreate(ejercicio_id=7, modo="progresion", sesiones_por_semana=3))


# ---------------- STATE (CU07) ----------------

DATOS = RegistroProgresoCreate(series_realizadas=3, repeticiones_realizadas=12, peso_realizado=20)


def test_programada_no_registra(db):
    r = _rutina(db, HOY + timedelta(days=3), HOY + timedelta(days=30))
    ctx = RutinaContexto(r, HOY, RegistroProgresoRepository(db))
    assert isinstance(ctx.estado, Programada)
    with pytest.raises(OperacionNoPermitida):
        ctx.registrar_progreso(_detalle(db, r), DATOS)


def test_en_curso_registra(db):
    r = _rutina(db, HOY - timedelta(days=2), HOY + timedelta(days=20))
    ctx = RutinaContexto(r, HOY, RegistroProgresoRepository(db))
    assert isinstance(ctx.estado, EnCurso)
    registro = ctx.registrar_progreso(_detalle(db, r), DATOS)
    assert registro.id is not None


def test_finalizada_no_registra_ni_edita(db):
    r = _rutina(db, HOY - timedelta(days=30), HOY - timedelta(days=1))
    ctx = RutinaContexto(r, HOY, RegistroProgresoRepository(db))
    assert isinstance(ctx.estado, Finalizada)  # Programada -> EnCurso -> Finalizada
    with pytest.raises(OperacionNoPermitida):
        ctx.registrar_progreso(_detalle(db, r), DATOS)
    with pytest.raises(OperacionNoPermitida):
        ctx.validar_edicion()


def test_bordes_de_fecha(db):
    r = _rutina(db, HOY, HOY)
    assert RutinaContexto(r, HOY, RegistroProgresoRepository(db)).nombre_estado == "en_curso"
    assert RutinaContexto(r, HOY + timedelta(days=1), RegistroProgresoRepository(db)).nombre_estado == "finalizada"


def test_contexto_sin_repo_para_validar_edicion(db):
    r = _rutina(db, HOY - timedelta(days=30), HOY - timedelta(days=1))
    with pytest.raises(OperacionNoPermitida):
        RutinaContexto(r, HOY).validar_edicion()


def test_hoy_usa_hora_de_bolivia():
    from datetime import datetime, timezone
    from app.domain.estado_rutina import hoy
    from app.domain.estado_rutina.reloj import ZONA_BOLIVIA
    assert hoy() == datetime.now(timezone.utc).astimezone(ZONA_BOLIVIA).date()

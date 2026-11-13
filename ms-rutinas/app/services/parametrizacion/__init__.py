"""Patrón STRATEGY - CU04 Detallar Rutina con Ejercicios.

Familia de algoritmos para calcular los parámetros de entrenamiento
(series, repeticiones, peso, descansos, RPE) de un DetalleRutina.
"""
from app.services.parametrizacion.estrategia_parametrizacion import (
    EstrategiaParametrizacion,
    ParametrizacionInvalida,
    ParametrosEntrenamiento,
)
from app.services.parametrizacion.parametrizador_detalle import ParametrizadorDetalle
from app.services.parametrizacion.parametros_manuales import ParametrosManuales
from app.services.parametrizacion.parametros_sugeridos import ParametrosSugeridos
from app.services.parametrizacion.progresion_carga import ProgresionCarga

__all__ = [
    "EstrategiaParametrizacion",
    "ParametrizacionInvalida",
    "ParametrosEntrenamiento",
    "ParametrizadorDetalle",
    "ParametrosManuales",
    "ParametrosSugeridos",
    "ProgresionCarga",
]

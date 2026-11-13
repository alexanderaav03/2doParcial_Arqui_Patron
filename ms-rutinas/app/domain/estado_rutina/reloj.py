from datetime import date, datetime, timedelta, timezone

# Bolivia está en UTC-4 todo el año (sin horario de verano).
ZONA_BOLIVIA = timezone(timedelta(hours=-4), name="America/La_Paz")


def hoy() -> date:
    """Fecha actual en Bolivia. No usar date.today(): en Docker el servidor
    suele estar en UTC y a las 20:00 de Bolivia ya sería 'mañana'."""
    return datetime.now(ZONA_BOLIVIA).date()

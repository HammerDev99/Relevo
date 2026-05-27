"""Cálculo de festivos colombianos y días hábiles (RN7).

Usa la librería `holidays` (holidays.CO), que aplica la Ley Emiliani
(Ley 51 de 1983) trasladando la mayoría de festivos al lunes.
"""

from __future__ import annotations

from datetime import date, timedelta

import holidays

from relevo.logger import get_logger
from relevo.models import Festivo
from relevo.result import Failure, Result, Success

logger = get_logger(__name__)

# La Ley Emiliani (Ley 51 de 1983) rige desde 1984.
ANIO_MINIMO = 1984


def festivos_de_anio(anio: int) -> Result[tuple[Festivo, ...], str]:
    """Retorna los festivos colombianos de `anio`, ordenados por fecha.

    Falla si `anio` no es un entero válido o es anterior a 1984.
    """
    if isinstance(anio, bool) or not isinstance(anio, int):
        return Failure(f"El año debe ser un entero, se recibió: {anio!r}")
    if anio < ANIO_MINIMO:
        return Failure(f"Año fuera de rango: {anio} (mínimo {ANIO_MINIMO})")

    feriados = holidays.country_holidays("CO", years=anio, language="es")
    festivos = tuple(
        Festivo(fecha=dia, nombre=str(nombre)) for dia, nombre in sorted(feriados.items())
    )
    logger.info("Festivos calculados para %d: %d encontrados", anio, len(festivos))
    return Success(festivos)


def dias_habiles(inicio: date, fin: date) -> Result[int, str]:
    """Cuenta días hábiles entre `inicio` y `fin` (ambos inclusive).

    Excluye sábados, domingos y festivos colombianos. Falla si `fin < inicio`.
    """
    if fin < inicio:
        return Failure(f"La fecha fin {fin.isoformat()} es anterior a inicio {inicio.isoformat()}")

    feriados = holidays.country_holidays(
        "CO", years=list(range(inicio.year, fin.year + 1)), language="es"
    )
    conteo = 0
    actual = inicio
    while actual <= fin:
        es_fin_de_semana = actual.weekday() >= 5  # 5=sábado, 6=domingo
        if not es_fin_de_semana and actual not in feriados:
            conteo += 1
        actual += timedelta(days=1)

    logger.info(
        "Días hábiles entre %s y %s: %d", inicio.isoformat(), fin.isoformat(), conteo
    )
    return Success(conteo)


def es_festivo(fecha: date) -> bool:
    """Verifica si una fecha específica es festivo en Colombia."""
    feriados = holidays.country_holidays("CO", years=fecha.year, language="es")
    return fecha in feriados

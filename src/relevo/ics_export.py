"""Exportación de festivos a formato iCalendar (.ics) para importar al Google Calendar."""

from __future__ import annotations

from relevo.festivos import festivos_de_anio
from relevo.result import Failure, Result, Success

_PRODID = "-//Relevo//Festivos CO//ES"


def exportar_ics(anio: int) -> Result[str, str]:
    """Genera el contenido `.ics` (VCALENDAR) con los festivos de `anio`.

    Cada festivo es un evento de día completo. Falla si el año es inválido.
    """
    resultado = festivos_de_anio(anio)
    if isinstance(resultado, Failure):
        return resultado

    lineas: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{_PRODID}",
        "CALSCALE:GREGORIAN",
    ]
    for festivo in resultado.value:
        fecha = festivo.fecha.strftime("%Y%m%d")
        lineas.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{fecha}-festivo@relevo",
                f"DTSTART;VALUE=DATE:{fecha}",
                f"SUMMARY:{festivo.nombre}",
                "TRANSP:TRANSPARENT",
                "END:VEVENT",
            ]
        )
    lineas.append("END:VCALENDAR")
    return Success("\r\n".join(lineas) + "\r\n")

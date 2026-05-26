"""Tests de SPEC-MVP-B3: exportación a .ics."""

from __future__ import annotations

from relevo.ics_export import exportar_ics
from relevo.result import Failure, Success


def test_ics_tiene_estructura_vcalendar() -> None:
    resultado = exportar_ics(2026)
    assert isinstance(resultado, Success)
    contenido = resultado.value
    assert contenido.startswith("BEGIN:VCALENDAR")
    assert contenido.rstrip().endswith("END:VCALENDAR")


def test_ics_un_vevent_por_festivo() -> None:
    resultado = exportar_ics(2026)
    assert isinstance(resultado, Success)
    assert resultado.value.count("BEGIN:VEVENT") == 18


def test_ics_anio_invalido_falla() -> None:
    resultado = exportar_ics(1983)
    assert isinstance(resultado, Failure)

"""Tests de SPEC-MVP-B1: cálculo de festivos colombianos."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from relevo.festivos import festivos_de_anio
from relevo.models import Festivo
from relevo.result import Failure, Success


def test_festivos_2026_tiene_18() -> None:
    resultado = festivos_de_anio(2026)
    assert isinstance(resultado, Success)
    assert len(resultado.value) == 18


def test_festivos_2026_incluye_traslado_ley_emiliani() -> None:
    # Reyes Magos (6 ene, martes) se traslada al lunes 12 ene.
    resultado = festivos_de_anio(2026)
    assert isinstance(resultado, Success)
    fechas = {f.fecha for f in resultado.value}
    assert date(2026, 1, 12) in fechas


def test_festivos_ordenados_por_fecha() -> None:
    resultado = festivos_de_anio(2026)
    assert isinstance(resultado, Success)
    fechas = [f.fecha for f in resultado.value]
    assert fechas == sorted(fechas)


def test_festivos_anio_antes_de_1984_falla() -> None:
    resultado = festivos_de_anio(1983)
    assert isinstance(resultado, Failure)


def test_festivos_no_entero_falla() -> None:
    resultado = festivos_de_anio("2026")  # type: ignore[arg-type]
    assert isinstance(resultado, Failure)


def test_festivos_bool_falla() -> None:
    resultado = festivos_de_anio(True)  # type: ignore[arg-type]
    assert isinstance(resultado, Failure)


def test_festivo_es_inmutable() -> None:
    festivo = Festivo(fecha=date(2026, 1, 1), nombre="Año Nuevo")
    with pytest.raises(FrozenInstanceError):
        festivo.fecha = date(2000, 1, 1)  # type: ignore[misc]


def test_festivo_to_dict_serializa_fecha_iso() -> None:
    festivo = Festivo(fecha=date(2026, 12, 25), nombre="Navidad")
    assert festivo.to_dict() == {"fecha": "2026-12-25", "nombre": "Navidad"}
